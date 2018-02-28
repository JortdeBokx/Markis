import hashlib
import mimetypes

import os
from flask_principal import identity_changed, AnonymousIdentity, Identity
from . import app, crowdServer, current_user
from flask import render_template, request, send_from_directory, redirect, url_for, flash, abort, send_file, \
	json, make_response, current_app, session
from flask_login import login_user, logout_user, login_required
from .models import Subject, Faculty, User, File, Favorite, db, Vote
from .forms import LoginForm, RegisterForm, UploadFileForm
from .util import util


@app.route('/')
def home():
	if not current_user.is_active:
		return redirect(url_for('login'))
	faculties = Faculty.query.all()
	subjects = Subject.query.join(Faculty, Subject.faculty_id == Faculty.faculty_id).add_columns(Subject.subject_id,
																								Subject.subject_name,
																								Subject.faculty_id,
																								Faculty.faculty_name)
	return render_template('home.html', subjects=subjects, faculties=faculties)


@app.route("/logout")
def logout():
	logout_user()

	# Remove session keys set by Flask-Principal
	for key in ('identity.name', 'identity.auth_type'):
		session.pop(key, None)

	# Tell Flask-Principal the user is anonymous
	identity_changed.send(current_app._get_current_object(),
						identity=AnonymousIdentity())
	flash("You are now successfully logged out", 'success')
	return redirect("/login", code=302)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate():
		# Get the password Hash from  the DB where username
		try:
			user = User(form.username.data)
		except ValueError:
			return render_template('login.html', error='Username not found', form=form)

		if user.authenticate(form.username.data, form.password.data):
			login_user(user, remember=form.keepLoggedIn.data)
			identity_changed.send(current_app._get_current_object(),
								identity=Identity(user.username))
		else:
			return render_template('login.html', error='Password incorrect', form=form)

		next_url = request.args.get('next')
		if not util.is_safe_url(next_url):
			return abort(400)
		return redirect(next_url or url_for('home'))
	else:
		return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		first_name = form.first_name.data
		last_name = form.last_name.data
		email = form.email.data
		password = form.password.data
		displayname = first_name + " " + last_name

		result = crowdServer.add_user(username, first_name=first_name, last_name=last_name, password=password,
									email=email,
									displayname=displayname)

		if result:
			flash("You are now successfully registered", 'success')
			return redirect(url_for('login'))
		else:
			# registration failed
			return render_template('register.html', error='Internal error, please try again', form=form)
	else:
		return render_template('register.html', form=form)


@app.route('/profile')
@login_required
def profile():
	response = make_response(redirect('https://my.cs-students.nl/crowd/console/user/viewprofile.action'))
	return response


@app.route('/subject/<subject_id>/')
@login_required
def subject(subject_id):
	subject_data_set = util.get_subject_data_set(subject_id)
	if subject_data_set is None:
		return render_template('404.html', reason="nosubject"), 404
	else:
		folders_to_show = util.get_subject_folders(subject_id)
		return render_template('subject.html', subjectDataSet=subject_data_set, folders=folders_to_show)


@app.route('/subject/<subject_id>/<path:subfolder>')
@login_required
def subjectfiles(subject_id, subfolder):
	subject_data_set = util.get_subject_data_set(subject_id)
	if subject_data_set is None:
		return render_template('404.html', reason="nosubject"), 404
	first_dir = subfolder.split('/')[0]
	if first_dir not in app.config['SUBJECT_SUBFOLDERS']:
		return render_template('404.html', reason="nopath"), 404
	else:
		if len(subfolder.split('/')) == 1:
			if first_dir in app.config['SUBJECT_SUBFOLDERS']:
				foldersToShow = util.get_folders_to_show(subject_id, subfolder)
				filesToShow = util.get_files_to_show(subject_id, subfolder, current_user.get_id())
				return render_template('files.html', folders=foldersToShow, files=filesToShow,
									subjectDataSet=util.get_subject_data_set(subject_id))
			else:
				return render_template('404.html', reason="nopath"), 404
		elif len(subfolder.split('/')) == 2:
			second_dir = subfolder.split('/')[1]
			if first_dir in app.config['SUBJECT_SUBFOLDERS'] and util.folder_has_contents(subject_id, subfolder):
				foldersToShow = util.get_folders_to_show(subject_id, subfolder)
				filesToShow = util.get_files_to_show(subject_id, subfolder, current_user.get_id())
				return render_template('files.html', folders=foldersToShow, files=filesToShow,
										subjectDataSet=util.get_subject_data_set(subject_id))
			else:
				return render_template('404.html', reason="nopath"), 404
		elif len(subfolder.split('/')) == 3:
			second_dir = subfolder.split('/')[1]
			third_dir = subfolder.split('/')[2]
			if first_dir in app.config['SUBJECT_SUBFOLDERS'] and util.folder_has_contents(subject_id, subfolder) and third_dir in {'questions', 'answers'}:
				foldersToShow = util.get_folders_to_show(subject_id, subfolder)
				filesToShow = util.get_files_to_show(subject_id, subfolder, current_user.get_id())
				return render_template('files.html', folders=foldersToShow, files=filesToShow,
									subjectDataSet=util.get_subject_data_set(subject_id))
			else:
				return render_template('404.html', reason="nopath"), 404
		else:
			return render_template('404.html', reason="nopath"), 404


@app.route(app.config['FILESTORE_PATH'] + '/<file_hash>')
@login_required
def get_file(file_hash):
	if util.file_exists(file_hash):
		file = File.query.filter(File.file_hash == file_hash).first()
		if not file:
			return make_response('File not Found', 404)
		file = file.__dict__
		filename = file['name']
		filetype = file['type']
		path = os.path.join(app.config['FILESTORE_DIR'], file_hash)
		resp = make_response(send_file(path, mimetype=filetype,
									as_attachment=False,
									attachment_filename=filename))
		resp.headers['Content-Disposition'] = "inline; filename=%s" % filename
		return resp

	else:
		return make_response('File not Found', 404)

@app.route('/favorites')
@login_required
def favorites():
	username = current_user.get_id()
	favorites = util.get_favorite_files(username)
	return render_template('favorites.html', favorites=favorites)


@app.route('/setfavorite', methods=["POST", "DELETE"])
def set_favorite():
	if request.method == "POST":
		if current_user.is_authenticated and current_user.is_active:
			username = current_user.get_id()
			file_id = int(request.json['fileid'])
			if file_id is not None or type(file_id) is not int:
				file_to_favorite = File.query.filter(File.file_id == file_id).first()
				if not file_to_favorite:
					return make_response('Invalid FileID', 400)
				file_to_favorite = file_to_favorite.__dict__
				if util.file_exists(file_to_favorite['file_hash']):
					database_has_entry = Favorite.query.filter(Favorite.file_id == file_id)\
						.filter(Favorite.user_username == username).first()
					if database_has_entry:
						Favorite.query.filter(Favorite.file_id == file_id).filter(Favorite.user_username == username).delete()
						db.session.commit()
					else:
						ins = Favorite(file_id=file_id, user_username=username)
						db.session.add(ins)
						db.session.commit()
					return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
				else:
					return make_response('File does not exist', 400)
			else:
				return make_response('Invalid FileID', 400)
		else:
			return abort(403)
	elif request.method == "DELETE":
		if current_user.is_authenticated and current_user.is_active:
			username = current_user.get_id()
			file_id = int(request.json['fileid'])
			if file_id is not None or type(file_id) is not int:
				file_to_favorite = File.query.filter(File.file_id == file_id).first()
				if not file_to_favorite:
					return make_response('Invalid FileID', 400)
				file_to_favorite = file_to_favorite.__dict__
				if util.file_exists(file_to_favorite['file_hash']):
					Favorite.query.filter(Favorite.file_id == file_id).filter(
						Favorite.user_username == username).delete()
					db.session.commit()
					return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
				else:
					return make_response('File does not exist', 400)
			else:
				return make_response('Invalid FileID', 400)
		else:
			return abort(403)
	else:
		return abort(405)


@app.route('/votefile', methods=['POST'])
def vote_file():
	if current_user.is_authenticated and current_user.is_active:
		if request.method == 'POST':
			username = current_user.get_id()
			file_id = request.json['fileid']
			newVote = request.json['vote']
			if type(file_id) == int and type(newVote) == int:
				file_for_vote = File.query.filter(File.file_id == file_id).first()
				if not file_for_vote:
					return make_response('Invalid FileID', 400)
				file_for_vote = file_for_vote.__dict__
				if util.file_exists(file_for_vote['file_hash']):
					currentVote = Vote.query.filter(Vote.file_id == file_id).filter(Vote.user_username == username).first()
					if currentVote is None:
						if newVote != 0:
							ins = Vote(file_id=file_id, user_username=username, vote=newVote)
							db.session.add(ins)
							db.session.commit()
							return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
						else:
							return make_response('Vote is same as current vote', 400)
					elif currentVote.vote == -1:
						if newVote == 1:
							existing_vote = Vote.query.filter(Vote.user_username == username).filter(
								Vote.file_id == file_id).first()
							existing_vote.vote = newVote
							db.session.commit()
							return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
						elif newVote == 0:
							Vote.query.filter(Vote.file_id == file_id).filter(Vote.user_username == username).delete()
							db.session.commit()
							return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
						else:
							return make_response('Vote is same as current vote', 400)
					elif currentVote.vote == 1:
						if newVote == -1:
							existing_vote = Vote.query.filter(Vote.user_username == username).filter(
								Vote.file_id == file_id).first()
							existing_vote.vote = newVote
							db.session.commit()
							return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
						elif newVote == 0:
							Vote.query.filter(Vote.file_id == file_id).filter(Vote.user_username == username).delete()
							db.session.commit()
							return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
						else:
							return make_response('Vote is same as current vote', 400)
					else:
						return make_response('Current vote cannot be found', 500)
				else:
					return make_response('Invalid FileID', 400)
			else:
				return make_response('Data types incorrect', 400)
		else:
			return make_response('Only POST requests accepted', 400)
	else:
		return abort(403)


@app.route('/form/getuploadform', methods=["GET", "POST"])
@login_required
def upload_file_form():
	# Initialise the form
	form = UploadFileForm(request.form)
	subjects = Subject.query.all()
	form.subject.choices = [('course', 'Course')]
	for g in subjects:
		g = g.__dict__
		form.subject.choices.append((g['subject_id'], g['subject_id'] + ' - ' + g['subject_name']))
	yearToShow = util.get_years_list()
	form.opt1.choices = yearToShow

	if request.method == "GET":
		form.opt1.default = yearToShow[-1][0]
		form.process()
		return render_template('uploadForm.html', form=form)

	elif request.method == "POST":
		uploader_username = current_user.get_id()
		subject_id = form.subject.data
		category = form.filetype.data
		opt1 = form.opt1.data
		opt2 = form.opt2.data
		file = request.files["file"]
		filename = file.filename
		if not file or filename == '':
			return json.dumps("No File attached"), 400, {'ContentType': 'application/json'}
		if not util.get_subject_data_set(subject_id):
			return json.dumps("Subject does not exist"), 400, {'ContentType': 'application/json'}

		file.save(os.path.join(app.root_path, app.config['FILESTORE_DIR'], filename))
		sha1 = hashlib.sha1()

		f = open(os.path.join(app.root_path, app.config['FILESTORE_DIR'], filename), 'rb')
		sha1.update(f.read())
		f.close()
		file_hash = sha1.hexdigest()
		os.rename(os.path.join(app.root_path, app.config['FILESTORE_DIR'], filename),
				os.path.join(app.root_path, app.config['FILESTORE_DIR'], file_hash))

		if subject_id and category:
			display_path = category
			if category == "exams" or category == "homework":
				if opt1 and opt2 != "type":
					YearPeriod = opt1 + "-" + str(int(opt1) + 1)
					display_path = display_path + "/" + YearPeriod + "/" + opt2
				else:
					return json.dumps("Second set of options not selected"), 400, {'ContentType': 'application/json'}
			if File.query.filter(File.file_hash == file_hash).all():
				return json.dumps("That file is already uploaded"), 400, {
					'ContentType': 'application/json'}
			db_file = File(file_hash=file_hash, name=filename, display_path=display_path,
						subject_id=subject_id, uploader_username=uploader_username, type=file.content_type)
			db.session.add(db_file)
			db.session.commit()
			return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
		else:
			return json.dumps("No subject or category selected"), 400, {'ContentType': 'application/json'}
	else:
		return abort(405)


@app.route('/removefile', methods=["POST"])
def removeFile():
	if current_user.is_authenticated and current_user.is_active and current_user.get_admin:
		if request.method == 'POST':
			fileid = int(request.json['fileid'])
			if fileid is not None and type(fileid) is int:
				file = File.query.filter(File.file_id == fileid).first()
				if file:
					os.remove(os.path.join(app.root_path, app.config['FILESTORE_DIR'], file.file_hash))
					File.query.filter(File.file_id == fileid).delete()
					db.session.commit()
					return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
				else:
					return make_response('File does not exist', 400)
			else:
				return make_response('Invalid FileID', 400)
	else:
		return abort(403)


#############################################
# 			Paths to static Files			#
#############################################


@app.route('/css/<path:filename>')
def css(filename):
	return send_from_directory('css', filename)


@app.route('/js/<path:filename>')
def javascript(filename):
	return send_from_directory('js', filename)


@app.route('/img/<path:filename>')
def image(filename):
	return send_from_directory('img', filename)


@app.route('/favicon.ico')
def favicon():
	return send_from_directory('img', 'favicon.ico')


#############################################
# 			Template Filters				#
#############################################


@app.template_filter('breadcrumb')
def get_breadcrumb_path(url):
	r = {'home': '/'}
	currpath = ''
	url_list = url.split('/')
	url_list = list(filter(('').__ne__, url_list))
	for section in url_list:
		currpath = currpath + '/' + section
		r[section] = currpath
	r.pop('subject')
	return r


@app.template_filter('file_icon')
def icon_fmt(mimetypestring):
	FILE_ICONS = app.config["FILE_ICONS"]
	try:
		major_type = mimetypestring.split('/')[0]
	except IndexError:
		return FILE_ICONS["default"]
	if major_type == "application":
		searchstring = mimetypestring
	else:
		searchstring = major_type + "/"

	if searchstring in FILE_ICONS:
		return FILE_ICONS[searchstring]
	else:
		return FILE_ICONS["default"]

#############################################
# 			     Error Pages    			#
#############################################


@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404


@app.errorhandler(403)
def page_not_found(e):
	return render_template('403.html'), 403


@app.errorhandler(418)
def page_not_found(e):
	return render_template('418.html'), 418


@app.errorhandler(500)
def page_not_found(e):
	return render_template('500.html'), 500
