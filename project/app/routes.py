from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, UserSubjectForm, BookAppointmentForm
# SubjectListForm, SubjectSelectForm
from app.models import User, UserRole, Subject, Appointment


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


# debug page to make sure subjects are adding and filtering correctly
@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    subjects = Subject.query.order_by(Subject.name.collate("NOCASE")).all()
    return render_template('subjects.html', title='Subjects', subjects=subjects)


# debug page to make sure appointments are adding and filtering correctly
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    appointments = Appointment.query.order_by(Appointment.created_date)
    return render_template('appointments.html', title='Appointmentss', appointments=appointments)


@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    form = UserSubjectForm()
    if form.validate_on_submit():
        subject = Subject.query.get(form.subject.data)
        if subject in current_user.my_subjects:
            flash(f'You are already enrolled in {subject.name}', 'warning')
        else:
            current_user.my_subjects.append(subject)
            db.session.commit()
            flash(f'You have successfully enrolled in {subject.name}!', 'success')
        return redirect(url_for('add_subject'))
    
    return render_template('add_subject.html', title='Add Subject', form=form)


@app.route('/remove_subject/<int:subject_id>')
@login_required
def remove_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject in current_user.my_subjects:
        current_user.my_subjects.remove(subject)
        db.session.commit()
        flash(f'You have successfully unenrolled from {subject.name}!', 'success')
    else:
        flash(f'You are not enrolled in {subject.name}', 'warning')
    return redirect(url_for('add_subject'))


@app.route('/explore')
@login_required
def explore():
    # Find tutors who share subjects with the current user
    form = BookAppointmentForm()
    tutors = User.query.filter(
        User.role == UserRole.TUTOR,  # Filter for tutors
        User.id != current_user.id,   # Exclude current user
        User.my_subjects.any(Subject.id.in_([s.id for s in current_user.my_subjects]))  # Share any subject
    ).all()
    
    # Group tutors by subject
    tutors_by_subject = {}
    for subject in current_user.my_subjects:
        subject_tutors = User.query.filter(
            User.role == UserRole.TUTOR,
            User.id != current_user.id,
            User.my_subjects.contains(subject)
        ).all()
        if subject_tutors:
            tutors_by_subject[subject] = subject_tutors
    
    return render_template('explore.html', 
                          title='Explore', 
                          tutors=tutors,
                          form=form,
                          tutors_by_subject=tutors_by_subject)


@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    print(request.form.to_dict())  # Debugging: See incoming data

    tutor_id = request.form.getlist('tutor_id')[-1]  # Ensure we get a valid tutor_id
    booking_date_str = request.form.get('booking_date')
    booking_time_str = request.form.get('booking_time')

    if not tutor_id or not booking_date_str or not booking_time_str:
        flash("Missing required fields", "danger")
        return redirect(url_for('explore'))

    try:
        tutor_id = int(tutor_id)
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        booking_time = datetime.strptime(booking_time_str, '%H:%M').time()

        tutor = User.query.get(tutor_id)
        if not tutor or tutor.role != UserRole.TUTOR:
            flash(f'Invalid tutor selection.', 'danger')
            return redirect(url_for('explore'))

        # Ensure the student is actually a STUDENT
        if current_user.role != UserRole.STUDENT:
            flash("Only students can book appointments.", "danger")
            return redirect(url_for('explore'))

        # Create the appointment
        appointment = Appointment(
            student_id=current_user.id,  # The student is the current user
            tutor_id=tutor.id,  # The tutor is from the form
            booking_date=booking_date,
            booking_time=booking_time
        )

        db.session.add(appointment)
        db.session.commit()

        flash(f"Appointment booked with {tutor.username} on {booking_date} at {booking_time}.", "success")
    except ValueError as e:
        flash(f"Invalid date/time format: {str(e)}", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error booking appointment: {str(e)}", "danger")

    return redirect(url_for('explore'))

