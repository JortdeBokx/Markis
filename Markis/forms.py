from wtforms import Form, StringField, PasswordField, BooleanField, SelectField, validators, ValidationError
from . import crowdServer


def is_username_duplicate(username):
	return crowdServer.user_exists(username)


def is_mail_duplicate(email):
	return crowdServer.email_exists(email)


class RegisterForm(Form):
	def validate_email(self, field):  # here is where the magic is
		if is_mail_duplicate(field.data):  # check if in database
			raise ValidationError("There already exists an account with that email.")

	def validate_username(self, field):  # here is where the magic is
		if is_username_duplicate(field.data):  # check if in database
			raise ValidationError("There already exists an account with that username.")

	username = StringField("Username", [validators.Length(min=3, max=100)],
						render_kw={"placeholder": "Username"})

	first_name = StringField("First Name", [validators.Length(min=1, max=50)], render_kw={"placeholder": "First Name"})
	last_name = StringField("Last Name", [validators.Length(min=1, max=50)], render_kw={"placeholder": "Last Name"})
	email = StringField("E-mail", [validators.Email(message="Please enter a valid email address")],
						render_kw={"placeholder": "Email"})

	password = PasswordField("Password", [validators.Length(min=8, max=64)], render_kw={"placeholder": "Password"})
	password2 = PasswordField("Confirm Password", [
		validators.Length(min=8, max=64),
		validators.EqualTo('password', message="Your password and confirmation don't match.")
	], render_kw={"placeholder": "Password Confirmation"})


class LoginForm(Form):
	username = StringField("Username", [validators.Length(min=3, max=35)], render_kw={"placeholder": "Username"})
	password = PasswordField("Password", [validators.Length(min=8, max=128)], render_kw={"placeholder": "Password"})
	keepLoggedIn = BooleanField("")


class UploadFileForm(Form):
	subject = SelectField('Subject', )
	filetype = SelectField('File Type', choices=[('category', 'Category'), ('exams', 'Exams'), ('homework', 'Homework'), ('literature', 'Literature'), ('misc','Miscellanious'), ('summaries','Summaries')])
	opt1 = SelectField('Released/Made',)
	opt2 = SelectField('Upload Type', choices=[('type', 'Type'), ('answers', 'Answers'), ('questions', 'Questions')])