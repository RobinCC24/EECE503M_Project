from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SelectMultipleField, validators, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password', message='Passwords must match.')])

class RoleForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=80)])
    permissions = SelectMultipleField('Permissions', coerce=int, render_kw={'multiple': True})
    submit = SubmitField('Submit')
