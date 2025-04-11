from datetime import datetime, timezone
from hashlib import md5
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, DateTime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from enum import Enum

user_subject = db.Table(
    "user_subject",
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id")),
    sa.Column("subject_id", sa.Integer, sa.ForeignKey("subject.id")),
)


class UserRole(Enum):
    STUDENT = "STUDENT"
    TUTOR = "TUTOR"
  


class Subject(db.Model):
    id:so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)
    topic: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)

    subject_appointments = db.relationship('Appointment', foreign_keys='Appointment.subject_id', 
                                           backref='subject', lazy='dynamic')
    requested_subjects = db.relationship('RequestedSubject', foreign_keys='RequestedSubject.subject_id',
                                            backref='requested_subject', lazy='dynamic')
    

class RequestedSubject(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<RequestedSubject Subject ID: {self.subject_id}, Student ID: {self.student_id}>"


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))
    umb_id: so.Mapped[str] = so.mapped_column(
        sa.String(8), unique=True)
    role: so.Mapped[UserRole] = so.mapped_column(sa.Enum(UserRole),
                                                 default=UserRole.STUDENT)
    
    # defines relationship to user_subjects table, and therefore subjects table
    my_subjects = so.relationship("Subject", secondary=user_subject, 
                                  backref="subject_user")

    user_requested_subjects = db.relationship('RequestedSubject', foreign_keys='RequestedSubject.student_id',
                                            backref='student_requester', lazy='dynamic')

    # defines relationship to appointments table for users with either student or tutor role
    student_appointments = db.relationship('Appointment', foreign_keys='Appointment.student_id', 
                                           backref='student', lazy='dynamic')
    tutor_appointments = db.relationship('Appointment', foreign_keys='Appointment.tutor_id', 
                                         backref='tutor', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))

    created_date = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    booking_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)

    # Track who last updated the appointment
    last_updated_by = db.Column(db.Enum(UserRole), nullable=True)

    def confirm(self, user_role):
        """Confirm the appointment."""
        self.status = 'confirmed'
        self.last_updated_by = user_role

    def cancel(self, user_role):
        """Cancel the appointment."""
        self.status = 'cancelled'
        self.last_updated_by = user_role

    def update(self, booking_date, booking_time, user_role):
        """Update the appointment details."""
        self.booking_date = booking_date
        self.booking_time = booking_time
        self.status = 'pending'
        self.last_updated_by = user_role

    def __repr__(self):
        return (f"<Appointment {self.id} - {self.booking_date} @ {self.booking_time} - "
                f"Status: {self.status}, Last Updated By: {self.last_updated_by}>")

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

    tutor = db.relationship('User', backref='availabilities', lazy=True)




@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))