from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from . import app, crowdServer, crowd_admin_group

db = SQLAlchemy(app)


class Subject(db.Model):
	__tablename__ = 'subjects'
	subject_id = db.Column(db.String(45), unique=True, nullable=False, primary_key=True)
	subject_name = db.Column(db.String(200), unique=True, nullable=False)
	faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.faculty_id'), unique=False, nullable=False)

	def __repr__(self):
		return '<Subject %r>' % self.subject_id


class File(db.Model):
	__tablename__ = 'files'
	file_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
	file_hash = db.Column(db.CHAR(40), unique=True, nullable=False)  # SHA-1 is always 40 chars long
	name = db.Column(db.String(200), unique=False, nullable=False)
	display_path = db.Column(db.String(200), unique=False, nullable=False)
	subject_id = db.Column(db.String(45), unique=False, nullable=False)
	type = db.Column(db.String(127), unique=False, nullable=False)  # 127 is the max length according to RFC 4288
	upload_date = db.Column(db.DATETIME, server_default=func.now(), nullable=False)
	uploader_username = db.Column(db.String(100), nullable=False)


class Faculty(db.Model):
	__tablename__ = 'faculties'
	faculty_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
	faculty_name = db.Column(db.String(100), unique=True, nullable=False)

	def __repr__(self):
		return '<Faculty %r>' % self.faculty_name


class Vote(db.Model):
	__tablename__ = 'user_file_vote'
	user_username = db.Column(db.String(100), unique=False, nullable=False, primary_key=True)
	file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), unique=False, nullable=False, primary_key=True)
	vote = db.Column(db.Integer, unique=False, nullable=False)


class Favorite(db.Model):
	__tablename__ = 'user_file_favorite'
	user_username = db.Column(db.String(100), unique=False, nullable=False, primary_key=True)
	file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), unique=False, nullable=False, primary_key=True)


class User:
	def __init__(self, username):
		if not crowdServer.user_exists(username):
			raise ValueError('User %s does not exist' % username)

		self.username = username
		crowd_user = crowdServer.get_user(self.username)
		self.first_name = crowd_user['first-name']
		self.last_name = crowd_user['last-name']
		self.displayname = crowd_user['display-name']
		self.email = crowd_user['email']
		self.isAdmin = crowdServer.get_groups(username).__contains__(crowd_admin_group)
		self.active = crowd_user['active']
		self._authenticated = False

	def get_id(self):
		return self.username

	def get_admin(self):
		return self.isAdmin

	def is_active(self):
		return self.active

	def is_anonymous(self):
		return False

	def is_authenticated(self):
		return self._authenticated

	def authenticate(self, username, password):
		self.username = username
		authenticated = crowdServer.auth_user(self.username, password)
		self._authenticated = (authenticated is not None)
		return self._authenticated

	def return_username(self):
		return self.username
