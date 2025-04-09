from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
import sqlalchemy as sa
from app import app, db, mail
from app.forms import LoginForm, RegistrationForm, EditProfileForm, UserSubjectForm, BookAppointmentForm, UpdateAppointmentForm, RequestClassForm
from app.models import User, UserRole, Subject, Appointment, RequestedSubject
from app.calendarplus import AppointmentCalendar


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.context_processor
def inject_user_role():
    return dict(UserRole=UserRole)





@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = BookAppointmentForm()

    # Other logic for appointments and requested subjects
    all_appointments = list(current_user.student_appointments) + list(current_user.tutor_appointments)
    pending_appointments = [appointment for appointment in all_appointments if appointment.status == 'pending']
    confirmed_appointments = [appointment for appointment in all_appointments if appointment.status == 'confirmed']
    pending_needs_approval = [
        appointment for appointment in pending_appointments
        if appointment.last_updated_by != current_user.role
    ]
    pending_waiting_for_other = [
        appointment for appointment in pending_appointments
        if appointment.last_updated_by == current_user.role
    ]
    requested_subjects = db.session.query(Subject).join(RequestedSubject).filter(
        RequestedSubject.student_id == current_user.id
    ).all()


    return render_template(
        'index.html',
        pending_needs_approval=pending_needs_approval,
        pending_waiting_for_other=pending_waiting_for_other,
        confirmed_appointments=confirmed_appointments,
        requested_subjects=requested_subjects,
        form=form,
    )


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


@app.route('/explore')
@login_required
def explore():
    form = BookAppointmentForm()

    if current_user.role == UserRole.STUDENT:
        # Find tutors who share subjects with the current user
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

        return render_template(
            'explore.html',
            title='Explore',
            tutors=tutors,
            form=form,
            tutors_by_subject=tutors_by_subject
        )

    elif current_user.role == UserRole.TUTOR:
        # Query all students who have requested classes
        requested_classes = db.session.query(RequestedSubject, User, Subject).join(
            User, RequestedSubject.student_id == User.id
        ).join(
            Subject, RequestedSubject.subject_id == Subject.id
        ).all()

        return render_template(
            'explore.html',
            title='Explore',
            requested_classes=requested_classes,
            form=form
        )


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = BookAppointmentForm()  # Create an instance of the form
    return render_template('user.html', user=user, form=form)


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


@app.route('/send-email', methods=['GET', 'POST'])
@login_required
def send_email():
    msg = Message("Hello from Flask", sender="noreply@example.com", recipients=["test@example.com"])
    msg.body = "This is a test email sent from Flask."
    mail.send(msg)
    return "Email sent!"


# SUBJECTS SYSTEM


@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    form = UserSubjectForm()

    # Handle POST requests from the explore page
    if request.method == 'POST' and 'subject_id' in request.form:
        subject_id = request.form.get('subject_id')
        subject = Subject.query.get(subject_id)
        if subject:
            if subject in current_user.my_subjects:
                flash(f'You already have {subject.name} added to your profile.', 'warning')
            else:
                current_user.my_subjects.append(subject)
                db.session.commit()
                flash(f'{subject.name} has been added to your profile.', 'success')
        else:
            flash('Invalid subject.', 'danger')
        return redirect(url_for('explore'))

    # Handle POST requests from the add_subject.html form
    if form.validate_on_submit():
        subject = Subject.query.get(form.subject.data)
        if subject:
            if subject in current_user.my_subjects:
                flash(f'You already have {subject.name} added to your profile.', 'warning')
            else:
                current_user.my_subjects.append(subject)
                db.session.commit()
                flash(f'You have successfully enrolled in {subject.name}!', 'success')
        else:
            flash('Invalid subject.', 'danger')
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
    return redirect(request.referrer or url_for('add_subject'))

@app.route('/request_class', methods=['GET', 'POST'])
@login_required
def request_class():
    if current_user.role != UserRole.STUDENT:
        flash("Only students can request classes.", "danger")
        return redirect(url_for('explore'))

    form = RequestClassForm(user_id=current_user.id)
    if form.validate_on_submit():
        # Check if the subject is already requested
        existing_request = db.session.query(RequestedSubject).filter_by(
            subject_id=form.subject.data,
            student_id=current_user.id
        ).first()

        if existing_request:
            flash("You have already requested this class.", "warning")
        else:
            # Add a new entry to the RequestedSubject table
            requested_subject = RequestedSubject(
                subject_id=form.subject.data,
                student_id=current_user.id
            )
            db.session.add(requested_subject)
            db.session.commit()
            flash("Your class request has been submitted successfully!", "success")
        return redirect(url_for('index'))

    return render_template('request_class.html', title='Request Class', form=form)


# APPOINTMENTS SYSTEM


@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    tutor_id = request.form.getlist('tutor_id')[-1]
    subject_id = request.form.get('subject_id')
    booking_date_str = request.form.get('booking_date')
    booking_time_str = request.form.get('booking_time')

    if not tutor_id or not booking_date_str or not booking_time_str or not subject_id:
        flash("Missing required fields", "danger")
        return redirect(url_for('explore'))

    try:
        tutor_id = int(tutor_id)
        subject_id = int(subject_id)
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        booking_time = datetime.strptime(booking_time_str, '%H:%M').time()

        tutor = User.query.get(tutor_id)
        subject = Subject.query.get(subject_id)

        if not tutor or tutor.role != UserRole.TUTOR:
            flash(f'Invalid tutor selection.', 'danger')
            return redirect(url_for('explore'))

        if not subject:
            flash(f'Invalid subject selection.', 'danger')
            return redirect(url_for('explore'))

        if current_user.role != UserRole.STUDENT:
            flash("Only students can book appointments.", "danger")
            return redirect(url_for('explore'))

        # Create the appointment
        appointment = Appointment(
            student_id=current_user.id,
            tutor_id=tutor.id,
            subject_id=subject.id,
            booking_date=booking_date,
            booking_time=booking_time,
            last_updated_by=current_user.role
        )

        db.session.add(appointment)
        db.session.commit()

        flash(f"Appointment booked with {tutor.username} for {subject.name} on {booking_date} at {booking_time}.", "success")
    except ValueError as e:
        flash(f"Invalid date/time format: {str(e)}", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error booking appointment: {str(e)}", "danger")

    return redirect(url_for('explore'))


@app.route('/confirm_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def confirm_appointment(appointment_id):
    # Fetch the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # Ensure the current user is the tutor for this appointment
    if appointment.last_updated_by == current_user.role:
        flash("You are not authorized to confirm this appointment.", "danger")
        return redirect(request.referrer or url_for('index'))

    try:
        # Confirm the appointment and set last_updated_by
        appointment.confirm(current_user.role)
        db.session.commit()
        flash(f"Appointment {appointment.id} has been confirmed.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while confirming the appointment: {str(e)}", "danger")

    return redirect(request.referrer or url_for('index'))


@app.route('/appointment_update/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def appointment_update(appointment_id):
    # Fetch the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # Ensure the current user is associated with the appointment
    if current_user.id not in [appointment.student_id, appointment.tutor_id]:
        flash("You are not authorized to update this appointment.", "danger")
        return redirect(request.referrer or url_for('index'))

    form = UpdateAppointmentForm()

    if form.validate_on_submit():
        try:
            # Update the appointment details
            appointment.update(
                booking_date=form.booking_date.data,
                booking_time=form.booking_time.data,
                user_role=current_user.role
            )
            db.session.commit()
            flash("The appointment has been successfully updated.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating the appointment: {str(e)}", "danger")

    # Pre-fill the form with the current appointment details
    form.booking_date.data = appointment.booking_date
    form.booking_time.data = appointment.booking_time

    return render_template('appointment_update.html', title='Update Appointment', form=form, appointment=appointment)


@app.route('/remove_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def remove_appointment(appointment_id):
    # Fetch the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # Check if the current user is associated with the appointment
    if current_user.id not in [appointment.student_id, appointment.tutor_id]:
        flash("You are not authorized to cancel this appointment.", "danger")
        return redirect(request.referrer or url_for('index'))

    try:
        # Cancel the appointment and set last_updated_by
        appointment.cancel(current_user.role)
        db.session.delete(appointment)
        db.session.commit()
        flash("The appointment has been successfully canceled.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while canceling the appointment: {str(e)}", "danger")

    return redirect(request.referrer or url_for('index'))


# DEBUG


# debug page to make sure appointments are adding and filtering correctly
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    appointments = Appointment.query.order_by(Appointment.created_date)
    return render_template('appointments.html', title='Appointments', appointments=appointments)

# debug page to make sure subjects are adding and filtering correctly
@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    subjects = Subject.query.order_by(Subject.name.collate("NOCASE")).all()
    return render_template('subjects.html', title='Subjects', subjects=subjects)


# DEVELOPMENT

@app.route('/api/events')
@login_required
def api_events():
    # Query appointments for the current user
    appointments = Appointment.query.filter(
        (Appointment.student_id == current_user.id) | (Appointment.tutor_id == current_user.id)
    ).all()

    # Convert appointments to FullCalendar's event format
    events = [
        {
            'id': appointment.id,  # Include the appointment ID
            'title': f"{appointment.subject.name} with {appointment.tutor.username if current_user.role == UserRole.STUDENT else appointment.student.username}",
            'start': f"{appointment.booking_date}T{appointment.booking_time}",  # Combine date and time
            'end': f"{appointment.booking_date}T{appointment.booking_time}",  # Optional: Add end time if needed
            'status': appointment.status,  # Include the status of the appointment
            'url': f"/appointment/{appointment.id}",  # Link to appointment details
            'description': f"Subject: {appointment.subject.name}, Status: {appointment.status}",  # Add a description
        }
        for appointment in appointments
    ]

    return jsonify(events)