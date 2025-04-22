from datetime import datetime, timezone, date, time
from hashlib import md5
import json
from time import time
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, DateTime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login, app
from enum import Enum

user_subject = db.Table(
    "user_subject",
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id")),
    sa.Column("subject_id", sa.Integer, sa.ForeignKey("subject.id")),
)


class UserRole(Enum):
    STUDENT = "student"
    TUTOR = "tutor"    


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
    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')
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
    
    last_message_read_time: so.Mapped[Optional[datetime]]
    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.sender_id', back_populates='author')
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.recipient_id', back_populates='recipient')
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(
        back_populates='user')
    alerts_received: so.WriteOnlyMapped['Alert'] = so.relationship(
        foreign_keys="Alert.recipient_id", back_populates="recipient", lazy="dynamic")
    alerts_caused: so.WriteOnlyMapped['Alert'] = so.relationship(
        foreign_keys="Alert.catalyst_id", back_populates="catalyst", lazy="dynamic")
    availabilities: so.WriteOnlyMapped['Availability'] = so.relationship(back_populates='tutor', cascade='all, delete-orphan')
    reviews_left: so.WriteOnlyMapped['Review'] = so.relationship(
        foreign_keys='Review.student_id', back_populates='student', cascade='all, delete-orphan')
    reviews_received: so.WriteOnlyMapped['Review'] = so.relationship(
        foreign_keys='Review.tutor_id', back_populates='tutor', cascade='all, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)
    
    def unread_message_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        query = sa.select(Message).where(Message.recipient == self,
                                         Message.timestamp > last_read_time)
        return db.session.scalar(sa.select(sa.func.count()).select_from(
            query.subquery()))
    
    def unread_alert_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        alerts_query = sa.select(Alert).where(Alert.recipient == self,
                                         Alert.timestamp > last_read_time)
        return db.session.scalar(sa.select(sa.func.count()).select_from(
            alerts_query.subquery()))

    def add_notification(self, name, data):
        db.session.execute(self.notifications.delete().where(
            Notification.name == name))
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n
    
    def add_availability(self, day_of_week: int, start_time: time, end_time: time) -> 'Availability':
        """Add a new availability slot for the tutor."""
        if self.role != UserRole.TUTOR:
            raise ValueError("Only tutors can set availability")
        
        if not (0 <= day_of_week <= 6):
            raise ValueError("Day of week must be between 0 (Monday) and 6 (Sunday)")
        
        availability = Availability(
            tutor_id=self.id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(availability)
        return availability
    
    @property
    def profile_image_url(self):
        return self.profile_image or 'default.jpg'
    profile_image = db.Column(db.String(128), default='default.jpg')
    profile_image = db.Column(db.String(128), default='default.jpg')


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))

    created_date: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    booking_date = db.Column(db.Date, nullable=False)
    booking_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False)
    actual_start_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    actual_end_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), default='confirmed', nullable=False)
    location: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)

    # Track who last updated the appointment
    last_updated_by = db.Column(db.Enum(UserRole), nullable=True)
    appointment_alert: so.WriteOnlyMapped['Alert'] = so.relationship(
        back_populates='alert_appointment', 
        passive_deletes=True
    )
    reviews: so.WriteOnlyMapped['Review'] = so.relationship(
        back_populates='appointment',
        passive_deletes=True  # optional, but recommended for ondelete to work
    )

    def confirm(self, user_role):
        """Confirm the appointment."""
        self.status = 'confirmed'
        self.last_updated_by = user_role

    def cancel(self, user_role):
        """Cancel the appointment."""
        self.status = 'cancelled'
        self.last_updated_by = user_role

    def update(self, booking_date, booking_time, user_role, location):
        """Update the appointment details."""
        self.location = location
        self.booking_date = booking_date
        self.booking_time = booking_time
        self.status = 'pending'
        self.last_updated_by = user_role

    def get_html_url(self):
        """Generate an HTML link for the appointment."""
        return f'<a href="/appointment/{self.id}">{self.subject.name} with {self.tutor.username}</a>'

    def __repr__(self):
        return (f"<Appointment {self.id} - {self.booking_date} @ {self.booking_time} - "
                f"Status: {self.status}, Last Updated By: {self.last_updated_by}>")


class Review(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    appointment_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('appointment.id', ondelete='SET NULL'), nullable=True
    )
    student_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), nullable=False)
    tutor_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    stars: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)  # 1-5
    text: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)

    # Relationships
    appointment: so.Mapped['Appointment'] = so.relationship(back_populates='reviews')
    student: so.Mapped['User'] = so.relationship(foreign_keys=[student_id], back_populates='reviews_left')
    tutor: so.Mapped['User'] = so.relationship(foreign_keys=[tutor_id], back_populates='reviews_received')

    def __repr__(self):
        return f"<Review {self.id} by Student {self.student_id} for Tutor {self.tutor_id} - {self.stars} stars>"


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    
    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Alert(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    
    subject: so.Mapped[str] = so.mapped_column(sa.String(140)) # subject/headline of the alert
    message: so.Mapped[str] = so.mapped_column(sa.String(140)) # relevant information
    category: so.Mapped[str] = so.mapped_column(sa.String(50), index=True, default='general') # what type of alert (booked appointment, canceled appointment, etc.)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    relevant_date = db.Column(db.Date)
    relevant_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True) # who is receiving the alert
    catalyst_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), nullable=True) 
    appointment_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Appointment.id), nullable=True) # appointment attached to the alert
    # Correctly define the recipient relationship
    recipient: so.Mapped[User] = so.relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="alerts_received"
    )
    catalyst: so.Mapped[User] = so.relationship(
        "User",
        foreign_keys=[catalyst_id],
        back_populates="alerts_caused",
        lazy="joined"
    )
    alert_appointment: so.Mapped[Appointment] = so.relationship(
        "Appointment",
        foreign_keys=[appointment_id],
        back_populates="appointment_alert",
        lazy="joined"
    )

    def __repr__(self):
        return '<Alert {}>'.format(self.message)


class Message(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                 index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                    index=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    
    author: so.Mapped[User] = so.relationship(
        foreign_keys='Message.sender_id',
        back_populates='messages_sent')
    recipient: so.Mapped[User] = so.relationship(
        foreign_keys='Message.recipient_id',
        back_populates='messages_received')

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                            index=True)
    timestamp: so.Mapped[float] = so.mapped_column(index=True, default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)

    user: so.Mapped[User] = so.relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(str(self.payload_json))


class Availability(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    tutor_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), nullable=False)
    day_of_week: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)  # 0-6 for Monday-Sunday
    start_time: so.Mapped[time] = so.mapped_column(sa.Time, nullable=False)
    end_time: so.Mapped[time] = so.mapped_column(sa.Time, nullable=False)
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)

    # Relationship to User model
    tutor: so.Mapped['User'] = so.relationship(back_populates='availabilities')

    def __repr__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f'<Availability {days[self.day_of_week]}: {self.start_time}-{self.end_time}>'

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))