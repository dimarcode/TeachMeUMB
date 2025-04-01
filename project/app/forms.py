from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, HiddenField, DateField, TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp
import sqlalchemy as sa
from app import db
from app.models import User, UserRole, Subject


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


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError('Please use a different username.')

class UserSubjectForm(FlaskForm):
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Subject')
    
    def __init__(self, *args, **kwargs):
        super(UserSubjectForm, self).__init__(*args, **kwargs)
        self.subject.choices = [(s.id, f"{s.name} - {s.topic}") for s in Subject.query.order_by(Subject.name).all()]
    

class BookAppointmentForm(FlaskForm):
    tutor_id = HiddenField("Tutor ID", validators=[DataRequired()])  # Hidden field to store tutor ID
    booking_date = DateField("Date", format='%Y-%m-%d', validators=[DataRequired()])
    booking_time = TimeField("Time", format='%H:%M', validators=[DataRequired()])
    submit = SubmitField("Book Appointment")

class UpdateAppointmentForm(FlaskForm):
    booking_date = DateField("New Date", format='%Y-%m-%d', validators=[DataRequired()])
    booking_time = TimeField("New Time", format='%H:%M', validators=[DataRequired()])
    submit = SubmitField("Update Appointment")