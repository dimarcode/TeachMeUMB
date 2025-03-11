from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
# SubjectListForm, SubjectSelectForm
from app.models import User, UserRole, Subject


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        role_value = form.role.data  # This will be "STUDENT" or "TUTOR" if you used the code above
        user = User(username=form.username.data,
                   email=form.email.data,
                   umb_id=form.umb_id.data,
                   role=UserRole(role_value))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    return render_template('user.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    subjects = Subject.query.order_by(Subject.name.collate("NOCASE")).all()
    return render_template('subjects.html', title='Subjects', subjects=subjects)


# @app.route('/add_classes', methods=['GET', 'POST'])
# @login_required
# def get_choices():
#     subject_list=[]
#     subjects = Subject.query.all()
#     for subject in subjects:
#         tup = (subject.name)
#         subject_list.append(tup)
#         return subject_list

# @app.route('/select_classes', methods=['GET', 'POST'])
# @login_required  # Ensure the user is logged in
# def select_classes():
#     # Create the form
#     form = SubjectListForm()
    
#     # Get all subjects for JS functionality
#     subjects = Subject.query.all()
#     subject_choices = [(s.id, f"{s.name} ({s.topic})") for s in subjects]
    
#     if form.validate_on_submit():
#         # Get the selected subject IDs
#         selected_subject_ids = [subform.subject.data for subform in form.subjects]
#         # Fetch the actual Subject objects
#         selected_subjects = Subject.query.filter(Subject.id.in_(selected_subject_ids)).all()
#         # Clear existing subjects and set the new ones
#         current_user.subjects = selected_subjects
#         # Commit changes to the database
#         db.session.commit()
#         flash('Your classes have been successfully selected!')
#         return redirect(url_for('index'))
        
#     # For GET requests, populate form with user's existing subjects if any
#     elif request.method == 'GET' and current_user.subjects:
#         # Clear existing form entries and add one for each of user's subjects
#         form.subjects.entries = []
#         for subject in current_user.subjects:
#             # Create a new entry for each subject
#             form.subjects.append_entry({'subject': subject.id})
    
#     return render_template('select_classes.html', 
#                            title='Select Classes', 
#                            form=form, 
#                            subject_choices=subject_choices)

# @app.route('/follow/<username>', methods=['POST'])
# @login_required
# def follow(username):
#     form = EmptyForm()
#     if form.validate_on_submit():
#         user = db.session.scalar(
#             sa.select(User).where(User.username == username))
#         if user is None:
#             flash(f'User {username} not found.')
#             return redirect(url_for('index'))
#         if user == current_user:
#             flash('You cannot follow yourself!')
#             return redirect(url_for('user', username=username))
#         current_user.follow(user)
#         db.session.commit()
#         flash(f'You are following {username}!')
#         return redirect(url_for('user', username=username))
#     else:
#         return redirect(url_for('index'))


# @app.route('/unfollow/<username>', methods=['POST'])
# @login_required
# def unfollow(username):
#     form = EmptyForm()
#     if form.validate_on_submit():
#         user = db.session.scalar(
#             sa.select(User).where(User.username == username))
#         if user is None:
#             flash(f'User {username} not found.')
#             return redirect(url_for('index'))
#         if user == current_user:
#             flash('You cannot unfollow yourself!')
#             return redirect(url_for('user', username=username))
#         current_user.unfollow(user)
#         db.session.commit()
#         flash(f'You are not following {username}.')
#         return redirect(url_for('user', username=username))
#     else:
#         return redirect(url_for('index'))
    

# @app.route('/explore')
# @login_required
# def explore():
#     page = request.args.get('page', 1, type=int)
#     query = sa.select(Post).order_by(Post.timestamp.desc())
#     posts = db.paginate(query, page=page,
#                         per_page=app.config['POSTS_PER_PAGE'], error_out=False)
#     next_url = url_for('explore', page=posts.next_num) \
#         if posts.has_next else None
#     prev_url = url_for('explore', page=posts.prev_num) \
#         if posts.has_prev else None
#     return render_template('index.html', title='Explore', posts=posts.items,
#                            next_url=next_url, prev_url=prev_url)


# @app.route('/customers', methods=['GET', 'POST'])
# @login_required
# def customers():
    
#     customers = Customer.query.order_by(Customer.last_name.collate("NOCASE")).all()
#     return render_template('customers.html', title='Customers', customers=customers)


# @app.route('/add_customer', methods=['GET', 'POST'])
# @login_required
# def add_customer():
#     form = AddCustomerForm()
#     if form.validate_on_submit():
#         new_customer = Customer(first_name=form.first_name.data, last_name=form.last_name.data, address=form.address.data, 
#                             city=form.city.data, state=form.state.data, zip=form.zip.data, phone=form.phone.data,  email=form.email.data)
#         db.session.add(new_customer)
#         db.session.commit()
#         flash('New customer added!')
#         return redirect(url_for('customers'))
#     return render_template('add_customer.html', title='Add Customer', form=form)


# @app.route('/orders', methods=['Get', 'POST'])
# @login_required
# def orders():
#     orders = Order.query.order_by(Order.date).all()
#     return render_template('orders.html', title='Orders', orders=orders)