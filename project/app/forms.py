from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, HiddenField, DateField, TimeField, IntegerField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email, EqualTo, Length, Regexp, NumberRange, Optional
import sqlalchemy as sa
from app import db
from app.models import User, UserRole, Subject, user_subject, Location
from flask_login import current_user


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class TestEmailForm(FlaskForm):
    submit = SubmitField('Send Test Email')

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
    profile_picture = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
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
            
class UploadWorkForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    subject_id = SelectField('Subject', coerce=int, validators=[Optional()])
    subject_other = StringField('Other Subject', validators=[Optional(), Length(max=50)])
    work_example = FileField('Upload Document', validators=[
        FileAllowed(['doc', 'docx', 'pdf'], 'Documents only!')
    ])
    upload_terms_agreement = BooleanField('Tutor Upload Agreement', 
                             validators=[DataRequired(message="You must agree to the terms to upload content")])
    submit = SubmitField('Upload Work Example')

    def __init__(self, *args, **kwargs):
        super(UploadWorkForm, self).__init__(*args, **kwargs)
        self.subject_id.choices = [(s.id, f"{s.name} - {s.topic}") for s in current_user.my_subjects]

class UserSubjectForm(FlaskForm):
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Subject')
    
    def __init__(self, *args, **kwargs):
        super(UserSubjectForm, self).__init__(*args, **kwargs)
        self.subject.choices = [(s.id, f"{s.name} - {s.topic}") for s in Subject.query.order_by(Subject.name).all()]
    
class BookAppointmentForm(FlaskForm):
    tutor_id = HiddenField("Tutor ID", validators=[DataRequired()])  # Hidden field to store tutor ID
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    booking_date = DateField("Date", format='%Y-%m-%d', validators=[DataRequired()])
    booking_time = TimeField("Time", format='%H:%M', validators=[DataRequired()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    directions = TextAreaField('Directions', validators=[Optional(), Length(max=200)])
    submit = SubmitField("Book Appointment")

    def __init__(self, *args, **kwargs):
        super(UserSubjectForm, self).__init__(*args, **kwargs)
        self.subject_id.choices = [(s.id, f"{s.name} - {s.topic}") for s in current_user.mysubjects]

    def __init__(self, *args, **kwargs):
        super(BookAppointmentForm, self).__init__(*args, **kwargs)
        self.location_id.choices = [(l.id, f"{l.name}") for l in Location.query.order_by(Location.name).all()]

class UpdateAppointmentForm(FlaskForm):
    booking_date = DateField("Date", format='%Y-%m-%d', validators=[DataRequired()])
    booking_time = TimeField("Time", format='%H:%M', validators=[DataRequired()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    directions = TextAreaField('Directions', validators=[Optional(), Length(max=200)])
    submit = SubmitField("Update Appointment")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location_id.choices = [(l.id, f"{l.name}") for l in Location.query.order_by(Location.name).all()]   

class RequestClassForm(FlaskForm):
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Request Class')

    def __init__(self, user_id, *args, **kwargs):
        super(RequestClassForm, self).__init__(*args, **kwargs)
        # Populate the dropdown with subjects associated with the user
        self.subject.choices = [
            (subject.id, f"{subject.name} - {subject.topic}")
            for subject in db.session.query(Subject)
            .join(user_subject, user_subject.c.subject_id == Subject.id)
            .filter(user_subject.c.user_id == user_id)
            .order_by(Subject.name)
            .all()
        ]

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class MessageForm(FlaskForm):
    message = TextAreaField(('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')


class BeginAppointmentForm(FlaskForm):
    start_time = TimeField('Actual Start Time', validators=[DataRequired()])
    end_time = TimeField('Actual End Time', validators=[DataRequired()])
    submit = SubmitField('Finish')


class ReviewAppointmentForm(FlaskForm):
    stars = IntegerField('Stars (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    text = TextAreaField('Review', validators=[Optional()])
    submit = SubmitField('Submit Review')


class AvailabilityForm(FlaskForm):
    day_of_week = SelectField('Day of Week', 
        choices=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday')
        ],
        coerce=int,  # This ensures the value is converted to an integer
        validators=[InputRequired()]
    )
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    submit = SubmitField('Add Availability')


class TestAvailabilityForm(FlaskForm):
    tutor_id = SelectField('Tutor', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Day of Week', 
        choices=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday')
        ],
        coerce=int,  # This ensures the value is converted to an integer
        validators=[InputRequired()]
    )
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Check Availability')