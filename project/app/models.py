from datetime import datetime, timezone
from hashlib import md5
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
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
    STUDENT = "student"
    TUTOR = "tutor"

# I may have to add columns for first name and last name later
class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)

# add system for verifying umb email
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
    
    my_subjects = so.relationship("Subject", secondary=user_subject, backref="subject_user")


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'


class Subject(db.Model):
     id:so.Mapped[int] = so.mapped_column(primary_key=True)
     name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)
     topic: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Item(db.Model):
        id: so.Mapped[int] = so.mapped_column(primary_key=True)
        item_name: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
        price: so.Mapped[float] = so.mapped_column(sa.Numeric(10, 2), nullable=False)