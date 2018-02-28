# File containing utility functions
#
# Please always provide a function description

from urllib.parse import urlparse, urljoin

import datetime

import os
from sqlalchemy import text
from sqlalchemy.sql import func
from Markis import app
from flask import request
from Markis.models import File, Subject, Faculty, Vote, Favorite, db, User


def is_safe_url(target):
	"""Check whether a url target is "safe"
			Args:
				target: The target URL.
			Returns:
				True:
					The target URL is safe to follow
				False:
					The target URL is not safe to follow
	"""

	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ('http', 'https') and \
		ref_url.netloc == test_url.netloc


def folder_has_contents(subject_id, sub_folder_path):
	"""Check whether a given sub-folder for a subject has contents
					Args:
						subject_id: The subject ID for which to check
						sub_folder_path: The (display) path for the folder for which to check
					Returns:
						True: The folder has contents
						False: the folder has no contents
			"""
	files = File.query.filter(File.subject_id == subject_id).filter(File.display_path.contains(sub_folder_path)).all()
	if len(files) <= 0:
		return False
	for file in files:
		file = file.__dict__
		if file_exists(file['file_hash']):
			return True
	return False


def get_subject_folders(subject_id):
	"""get the list of folders to show for a specific subject
				Args:
					subject_id: The subject ID for which to check sub-folders
				Returns:
					List:
						String: Folder Name
						boolean: Folder has content
		"""
	folders_to_show = []
	folders = app.config['SUBJECT_SUBFOLDERS']
	for subFolder in folders:
		info = {'name': subFolder, 'hasContent': folder_has_contents(subject_id, subFolder)}
		folders_to_show.append(info)
	return folders_to_show


def get_subject_data_set(subject_id):
	"""get all data regarding a subject
					Args:
						subject_id: The subject ID for which to get all data
					Returns:
						Dict:
							Subject data
			"""
	return Subject.query.join(Faculty, Subject.faculty_id == Faculty.faculty_id) \
		.add_columns(Subject.subject_id,
					Subject.subject_name,
					Subject.faculty_id,
					Faculty.faculty_name).filter(Subject.subject_id == subject_id).one()


def get_folders_to_show(subject_id, subfolder):
	"""get all folders to show in a certain subfolder
						Args:
							subfolder: The subfolder for which to get folders
							subject_id: the subject ID in which we're looking
						Returns:
							List:
								Dict:
									name: Folders name
									hasContent: Folder has content
				"""
	first_subfolder = subfolder.split('/')[0]
	nrof_subfolders = len(subfolder.split('/'))

	folders_to_show = []
	if first_subfolder not in {'exams', 'homework'}:
		return []
	elif first_subfolder in {'exams', 'homework'}:
		if nrof_subfolders == 1:
			# show year periods for which files exist
			display_paths = File.query.filter(File.display_path.like(first_subfolder + '%'))\
				.filter(File.subject_id == subject_id).with_entities(File.display_path).all()
			for path in display_paths:
				path = dict(zip(path.keys(), path))
				yearperiod = {'name': path['display_path'].split('/')[1], 'hasContent': True}  # True as always contains files
				folders_to_show.append(yearperiod)
		if nrof_subfolders == 2:
			# return questions/answer folders, regardless of content
			last_folders = [{'name': "questions", 'hasContent': folder_has_contents(subject_id, subfolder + "/" + "questions")},
							{'name': "answers", 'hasContent': folder_has_contents(subject_id, subfolder + "/" + "answers")}]
			folders_to_show = last_folders
	return folders_to_show


def get_user_file_vote(file_id, username):
	"""get the vote of a user on a file
		Args:
			file_id: The file id for which to check votes
			username: username for whom to get the vote
		Returns:
			Integer:
				the vote of a user (+1, -1 or 0)
	"""
	vote = Vote.query.filter(Vote.file_id == file_id).filter(Vote.user_username == username).first()
	if not vote:
		return 0
	else:
		return vote.vote


def get_user_file_favorite(file_id, username):
	"""get the favorite of a user on a file
			Args:
				file_id: The file id for which to check favorites
				username: username for whom to get the favorite
			Returns:
				Boolean:
					whether the user has favorited the file
	"""
	favorite = Favorite.query.filter(Favorite.file_id == file_id).filter(Favorite.user_username == username).first()
	if not favorite:
		return False
	else:
		return True


def file_exists(file_hash):
	"""
		checks whether a file exists on disk
		:param file_hash: the hash of the file for which to check it's existence
		:return: Boolean whether it exists or not
		"""
	file_path = os.path.join(app.root_path, app.config["FILESTORE_DIR"], file_hash)
	return os.path.isfile(file_path)


def get_file_size(file_hash):
	"""
	gets the size of a file formatted in b, kb, mb or gb
	:param file_hash: the hash of the file for which we want to calculate the size
	:return: String containing the file's size in bytes, kilobytes, megabytes or gigabytes
	"""

	file_path = os.path.join(app.root_path, app.config["FILESTORE_DIR"], file_hash)
	try:
		file_size = os.path.getsize(file_path)
	except FileNotFoundError:
		return None
	if file_size >= (1024**3):
		file_size_string = str(round(file_size/(1024**3), 1)) + " GB"
	elif file_size >= (1024**2):
		file_size_string = str(round(file_size / (1024 ** 2), 1)) + " MB"
	elif file_size >= 1024:
		file_size_string = str(round(file_size / 1024, 1)) + " Kb"
	else:
		file_size_string = str(round(file_size, 1)) + " b"
	return file_size_string


def get_files_to_show(subject_id, subfolder, username):
	"""get all files to show in a certain subfolder
		Args:
			subfolder: The subfolder for which to get files
			subject_id: the subject ID in which we're looking
			username: username for current user (used to get votes)
		Returns:
			Dict:
				Files
	"""
	files = []
	# I know, should be with models to allow non-sql server to process it as well
	# so please feel free to translate this mess. If you do I'll buy you a beer
	s = text(
		"SELECT files.file_id, files.name, files.file_hash, files.type, DATE(files.upload_date) AS upload_date, "
		"IFNULL(SUM(user_file_vote.vote), 0) AS votes, files.uploader_username "
		"FROM files LEFT JOIN user_file_vote ON user_file_vote.file_id = files.file_id "
		"WHERE files.display_path = :p and files.subject_id = :s;")
	files_in_dir = db.engine.execute(s, p=subfolder, s=subject_id).fetchall()

	for file in files_in_dir:
		file = dict(zip(file.keys(), file))
		if file['file_id'] is not None:
			if file_exists(file["file_hash"]):
				try:
					file['uploader_displayname'] = User(file['uploader_username']).displayname
				except ValueError:
					file['uploader_displayname'] = file['uploader_username']  # if user is not found, just show his username
				file['user_vote'] = get_user_file_vote(file['file_id'], username)
				file['user_favorite'] = get_user_file_favorite(file['file_id'], username)
				file['size'] = get_file_size(file['file_hash'])
				file['downloadpath'] = app.config['FILESTORE_PATH'] + "/" + file['file_hash']

				files.append(file)
	return files


def get_years_list():
	"""get all year periods
		Returns:
			Tuple:
				first year of period: String for year period
					"""
	INITIAL_YEAR = app.config['INITIAL_YEAR']
	initialPeriod = str(INITIAL_YEAR) + " - " + str(INITIAL_YEAR + 1) + " (and earlier)"
	years = [(INITIAL_YEAR, initialPeriod)]
	now = datetime.datetime.now()
	currentYear = now.year
	if now.month < 8:
		currentYear -= 1  # if between jan and august, make sure currentYear is first year of year period
	for year in range(INITIAL_YEAR + 1, currentYear + 1):
		yearPeriod = str(year) + " - " + str(year + 1)
		years.append((year, yearPeriod))
	return years


def get_favorite_files(username):
	"""
	get all files a user has favorited
	:param username: the username of the use for whom to get the favorites
	:return: List of files as dictionaries
	"""
	files_to_show = []
	file_list = db.session.query(Favorite.file_id, Favorite.user_username, File.name, File.type, File.file_hash,
								func.DATE(File.upload_date).label("upload_date"), File.display_path, File.uploader_username, File.subject_id).filter(
								Favorite.user_username == username).join(
								File, Favorite.file_id == File.file_id).all()
	if not file_list:
		return []
	for file in file_list:
		file = dict(zip(file.keys(), file))
		if file_exists(file["file_hash"]):
			file['size'] = get_file_size(file['file_hash'])
			file['downloadpath'] = app.config['FILESTORE_PATH'] + "/" + file['file_hash']
			files_to_show.append(file)
	return files_to_show
