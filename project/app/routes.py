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
        role_value = form.role.data
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
    # Query to fetch all subjects for the user
    # subjects = db.session.execute(
    #     sa.select(Subject).join(user_subjects).where(user_subjects.c.user_id == user.id)
    # ).scalars().all()
    
    return render_template('user.html', user=user, subjects=subjects)

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

# @app.route('/my_subjects', methods=['GET', 'POST'])
# @login_required
# def my_subjects():
#     form = SubjectSelectForm()
#     if form.validate_on_submit():
#         subject_name = form.subject_name.data
#         subject = Subject.query.filter_by(name=subject_name).first()
        
#         if not subject:
#             flash('Subject not found.', 'danger')
#             return redirect(url_for('my_subjects'))
        
#         if subject in current_user.my_subject:
#             flash('You already have this subject in your list.', 'warning')
#             return redirect(url_for('my_subjects'))
        
#         # Add the subject to the user's subjects
#         current_user.my_subject.append(subject)
#         db.session.commit()
        
#         flash(f'Subject "{subject.name}" added successfully.', 'success')
#         return redirect(url_for('my_subjects'))
    
#     subjects = Subject.query.all()
    
#     # Render the template with the form, user's current subjects, and all available subjects
#     return render_template('my_subjects.html', 
#                           form=form,
#                           user_subjects=current_user.my_subject,
#                           subjects=subjects)

# @app.route('/remove_subject/<int:subject_id>', methods=['POST'])
# @login_required
# def remove_subject(subject_id):
#     subject = Subject.query.get_or_404(subject_id)
    
#     if subject in current_user.my_subject:
#         current_user.my_subject.remove(subject)
#         db.session.commit()
#         flash(f'Subject "{subject.name}" removed successfully.', 'success')
#     else:
#         flash('Subject not found in your list.', 'danger')
        
#     return redirect(url_for('my_subjects'))