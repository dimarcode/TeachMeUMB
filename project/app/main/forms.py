from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, HiddenField, DateField, TimeField
from wtforms.validators import ValidationError, DataRequired, Length
import sqlalchemy as sa
from app import db
from app.models import User, UserRole, Subject, user_subject


class TestEmailForm(FlaskForm):
    submit = SubmitField('Send Test Email')


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