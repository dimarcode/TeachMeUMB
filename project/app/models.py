from datetime import datetime, timezone
from hashlib import md5
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login


followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)

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
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

# user note
    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )


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


class Customer(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    first_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, nullable=False)
    last_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, nullable=False)
    address: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    city: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    state: so.Mapped[Optional[str]] = so.mapped_column(sa.String(2))
    zip: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10))
    phone: so.Mapped[Optional[str]] = so.mapped_column(sa.String(20))
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, nullable=False)

    orders: so.Mapped[list['Order']] = so.relationship('Order', back_populates="customer")

    def __repr__(self):
        return '<Customer {}>'.format(self.email)
    

class Item(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    item_name: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    price: so.Mapped[float] = so.mapped_column(sa.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f"<Item {self.item_name} - ${self.price}>"

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Order(db.Model):
    order_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    customer_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('customer.id'), nullable=False)
    order_number: so.Mapped[int] = so.mapped_column(nullable=False, unique=True)
    date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    customer: so.Mapped['Customer'] = so.relationship(back_populates="orders")
 #    order_items: so.Mapped[list['OrderLineItem']] = so.relationship(back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number} - Customer {self.customer_id}>"



# Orders and line items ---------------------------------------------------------------------------------------------------



# class OrderLineItem(db.Model):
#     order_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('order.order_id'), primary_key=True)
#     seq: so.Mapped[int] = so.mapped_column(primary_key=True)
#     item_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('item.id'), nullable=False)
#     qty: so.Mapped[int] = so.mapped_column(nullable=False)

#     order: so.Mapped['Order'] = so.relationship(back_populates="order_items")
#     item: so.Mapped['Item'] = so.relationship()

#     def __repr__(self):
#         return f"<OrderLineItem Order {self.order_id} Seq {self.seq} - Item {self.item_id} x {self.qty}>"

# ----------------------------------------------------------------------------------------------------------------------------



# following posts query (not including their own posts)

    # def following_posts(self):
    #     Author = so.aliased(User)
    #     Follower = so.aliased(User)
    #     return (
    #         sa.select(Post)
    #         .join(Post.author.of_type(Author))
    #         .join(Author.followers.of_type(Follower))
    #         .where(Follower.id == self.id)
    #         .order_by(Post.timestamp.desc())
    #     )    

# class Customer(db.Model): 
#     id: so.Mapped[int] = so.mapped_column(primary_key=True)
#     first_name: so.Mapped[str] = so.mapped_column(sa.String(50))
#     last_name: so.Mapped[str] = so.mapped_column(sa.String(50))
#     address: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
#     city: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50))
#     state: so.Mapped[Optional[str]] = so.mapped_column(sa.String(2))
#     zip: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10))
#     phone1: so.Mapped[str] = so.mapped_column(sa.String(15))
#     email: so.Mapped[str] = so.mapped_column(
#         sa.String(100), index=True, unique=True)
    
#     transactions: so.WriteOnlyMapped['Transaction'] = so.relationship(
#         back_populates='customers')

#     def __repr__(self):
#         return '<Customer {}>'.format(self.custID)

# class Transaction(db.Model):
    
#     id: so.Mapped[int] = so.mapped_column(primary_key=True)
#     cust_id: so.Mapped[int] = so.mapped_column(
#         sa.ForeignKey(Customer.id), index=True)
#     date: so.Mapped[datetime] = so.mapped_column(
#         index=True, default=lambda: datetime.now(timezone.utc))
#     total: so.Mapped[float] = so.mapped_column(
#         sa.Numeric(10, 2), nullable=False)
    
#     # Relationship to the Customer table
#     customers: so.WriteOnlyMapped['Customer'] = so.relationship(
#         back_populates='transactions')
    
#     def __repr__(self):
#         return '<transaction {}>'.format(self.transaction_id)

# class Item(db.Model):
#     __tablename__ = 'items'
    
#     itemID: so.Mapped[int] = so.mapped_column(primary_key=True)
#     itemname: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False, index=True)
#     price: so.Mapped[float] = so.mapped_column(sa.Numeric(10, 2), nullable=False)
    
#     def __repr__(self):
#         return '<Item {}>'.format(self.itemID)
    

    
# class LineItem(db.Model):
#     __tablename__ = 'lineitems'
    
#     lineID: so.Mapped[int] = so.mapped_column(primary_key=True)
#     transaction_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('transaction.transaction_id'), primary_key=True, index=True)
#     itemID: so.Mapped[int] = so.mapped_column(sa.ForeignKey('items.itemID'), nullable=False, index=True)
#     quantity: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    
#     # Relationships to the transaction and Item tables
#     transaction: so.Mapped["transaction"] = so.relationship(back_populates="lineitems")
#     item: so.Mapped["Item"] = so.relationship()
    
#     __table_args__ = (
#         sa.UniqueConstraint('lineID', 'transaction_id', name='uix_lineitem_transaction'),
#     )
    
#     def __repr__(self):
#         return '<LineItem {}-{}>'.format(self.transaction_id, self.lineID)