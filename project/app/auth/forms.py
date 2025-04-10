from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Regexp
import sqlalchemy as sa
from app import db
from app.models import User, UserRole


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    umb_id = StringField(
        'Umass Boston ID', validators=[DataRequired(), Regexp(r'^\d{8}$', message="Must be exactly 8 digits")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    # allows the user to choose if they are a student or tutor
    role = SelectField('Student or Tutor?', 
                       choices=[
                           (UserRole.STUDENT.value, "Student"), 
                           (UserRole.TUTOR.value, "Tutor")
                       ],
                       validators=[DataRequired()])  # Make sure it handles strings correctly
    
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_umb_id(self, umb_id):
        user = db.session.scalar(sa.select(User).where(
            User.umb_id == umb_id.data))
        if user is not None:
            raise ValidationError('This Umass Boston ID is already registered.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')
        

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')