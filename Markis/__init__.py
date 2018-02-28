from .util import crowd
from flask import Flask
from flask_login import LoginManager, current_user
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed

app = Flask(__name__, instance_relative_config=True, static_url_path='/static')
app.config.from_object('config')
app.config.from_pyfile('config.py')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "You need to be logged in to view this page!"

principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))

crowd_url = app.config['CROWD_API_URL']
crowd_user = app.config['CROWD_API_USER']
crowd_pass = app.config['CROWD_API_PASS']
crowd_admin_group = app.config['CROWD_API_ADMIN_GROUP']
crowdServer = crowd.Crowd(crowd_url, crowd_user, crowd_pass)


@login_manager.user_loader
def load_user(username):
	try:
		return User(username)
	except:
		return None


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
	# Set the identity user object
	identity.user = current_user

	# Add the UserNeed to the identity
	if hasattr(current_user, 'username'):
		identity.provides.add(UserNeed(current_user.get_id()))
		if current_user.isAdmin:
			identity.provides.add(RoleNeed('admin'))


from . import views, models
from Markis.models import db, User


def create_app():
	db.init_app(app)
	db.create_all()
	return app
