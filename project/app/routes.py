from datetime import datetime, timezone, time, timedelta
from urllib.parse import urlsplit
import pytz
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_moment import moment
import sqlalchemy as sa
from app import app, db, mail
from app.forms import LoginForm, RegistrationForm, EditProfileForm, UserSubjectForm, \
BookAppointmentForm, UpdateAppointmentForm, RequestClassForm, MessageForm, ResetPasswordRequestForm, \
ResetPasswordForm, AvailabilityForm, TestAvailabilityForm, BeginAppointmentForm, ReviewAppointmentForm
from app.models import User, UserRole, Subject, Appointment, RequestedSubject, Message, \
Notification, Alert, Availability, Review
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


###############
# AUTH SYSTEM #
###############


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


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)



########################
# HOMEPAGE / DASHBOARD #
########################


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = BookAppointmentForm()
    # Query appointments for the current user
    appointments = Appointment.query.filter(
        (Appointment.student_id == current_user.id) | (Appointment.tutor_id == current_user.id)
    ).all()


    # Other logic for appointments and requested subjects


    all_appointments = list(current_user.student_appointments) + list(current_user.tutor_appointments)
    pending_appointments = [appointment for appointment in all_appointments if appointment.status == 'pending']
    completed_appointments = [appointment for appointment in all_appointments if appointment.status == 'completed']
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
        completed_appointments=completed_appointments,
        requested_subjects=requested_subjects,
        form=form,
        UserRole=UserRole,
    )


@app.route('/api/events') # Gathers events for the calendar
@login_required
def api_events():
    appointments = Appointment.query.filter(
        (Appointment.student_id == current_user.id) | (Appointment.tutor_id == current_user.id)
    ).all()

    events = [
        {
            'id': appointment.id,
            'title': f"{appointment.subject.name} with {appointment.tutor.username if current_user.role == UserRole.STUDENT else appointment.student.username}",
            'start': appointment.booking_time.astimezone(timezone.utc).isoformat(),
            'end': (appointment.booking_time.astimezone(timezone.utc) + timedelta(hours=1)).isoformat(),
            'status': appointment.status,
            'url': f"/appointment/{appointment.id}",
            'description': f"Subject: {appointment.subject.name}, Status: {appointment.status}",
        }
        for appointment in appointments
    ]

    return jsonify(events)



################
# USER PROFILE #
################


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = BookAppointmentForm()  # Create an instance of the form
    return render_template('user.html', user=user, form=form, UserRole = UserRole)


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



#######################
# APPOINTMENTS SYSTEM #
#######################


@app.route('/explore') # Find tutors or students who have requested classes
@login_required
def explore():
    form= BookAppointmentForm()
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
            tutors_by_subject=tutors_by_subject,
            UserRole = UserRole
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
            form=form,
            requested_classes=requested_classes,
            UserRole = UserRole
        )


@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    tutor_id = request.args.get('tutor_id', type=int)
    if not tutor_id:
        flash("Invalid tutor selected.", "danger")
        return redirect(url_for('explore'))

    tutor = User.query.get_or_404(tutor_id)

    form = BookAppointmentForm(tutor_id=tutor_id)
    form.tutor_id.validators = []
    # Populate the subject dropdown with shared subjects
    form.subject_id.choices = [
        (subject.id, f"{subject.name} - {subject.topic}")
        for subject in tutor.my_subjects if subject in current_user.my_subjects
    ]

    if request.method == 'POST' and form.validate_on_submit():
        try:
            tutor = User.query.get_or_404(tutor_id)
            subject_id = form.subject_id.data
            booking_date = form.booking_date.data
            booking_time = form.booking_time.data

            # Combine date and time as UTC
            booking_datetime = datetime.combine(
                booking_date,
                booking_time,
                tzinfo=timezone.utc
            )

            subject = Subject.query.get(subject_id)
            if not subject:
                flash("Invalid subject selection.", "danger")
                return redirect(url_for('book_appointment', tutor_id=tutor_id))

            if current_user.role != UserRole.STUDENT:
                flash("Only students can book appointments.", "danger")
                return redirect(url_for('explore'))

            # Create the appointment
            appointment = Appointment(
                student_id=current_user.id,
                tutor_id=tutor.id,
                subject_id=subject.id,
                booking_date=booking_date,
                booking_time=booking_datetime,
                last_updated_by=current_user.role
            )
            db.session.add(appointment)
            db.session.commit()

            # Create an alert for the tutor
            alert = Alert(
                recipient_id=tutor.id,
                catalyst_id=current_user.id,
                appointment_id=appointment.id,
                category='book_appointment',
                relevant_date=booking_date,
                relevant_time=booking_datetime,
                subject="New Appointment Booked",
                message=f"booked an appointment with you for tutoring in {subject.name}"
            )
            db.session.add(alert)
            db.session.commit()

            flash(f"Appointment booked with {tutor.username} for {subject.name}. They have been sent an alert.", "success")
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error booking appointment: {str(e)}", "danger")

    return render_template('book_appointment.html', form=form, tutor=tutor)


@app.route('/appointment/<int:appointment_id>/begin', methods=['GET', 'POST']) # Begin an appointment
@login_required
def begin_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    form = BeginAppointmentForm()
    if form.validate_on_submit():
        appointment.actual_start_time = datetime.combine(appointment.booking_date, form.start_time.data)
        appointment.actual_end_time = datetime.combine(appointment.booking_date, form.end_time.data)

        db.session.commit()
        return redirect(url_for('review_appointment', appointment_id=appointment.id))
    return render_template('begin_appointment.html', form=form, appointment=appointment)


@app.route('/appointment/<int:appointment_id>/review', methods=['GET', 'POST']) # Review the tutor
@login_required
def review_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    form = ReviewAppointmentForm()
    if form.validate_on_submit():
        review = Review(
            appointment_id=appointment.id,
            student_id=current_user.id,
            tutor_id=appointment.tutor_id,
            stars=form.stars.data,
            text=form.text.data
        )
        db.session.add(review)
        appointment.status = 'completed'
        db.session.commit()
        flash(f"Your appointment with {appointment.tutor.username} has been successfully completed! Thanks for your review.", "success")
        return redirect(url_for('index'))
    return render_template('review_appointment.html', form=form, appointment=appointment)


@app.route('/confirm_appointment/<int:appointment_id>', methods=['POST']) # Confirm updates to an appointment
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


@app.route('/appointment_update/<int:appointment_id>', methods=['GET', 'POST']) # Change details of an appointment; date, time
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
            # Combine date and time into a datetime object
            booking_date = form.booking_date.data
            booking_time = form.booking_time.data
            if booking_date and booking_time:
                booking_datetime = datetime.combine(booking_date, booking_time)
            else:
                booking_datetime = appointment.booking_time  # fallback

            # Update the appointment details
            appointment.update(
                booking_date=booking_date,
                booking_time=booking_datetime,
                user_role=current_user.role
            )
            db.session.commit()
            flash("The appointment has been successfully updated! An alert has been sent.", "success")

            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating the appointment: {str(e)}", "danger")


    # Pre-fill the form with the current appointment details
    form.booking_date.data = appointment.booking_date
    # Set the time part for the form (expects a time object)
    form.booking_time.data = appointment.booking_time.time() if appointment.booking_time else None

    return render_template('appointment_update.html', title='Update Appointment', form=form, appointment=appointment)


@app.route('/remove_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def remove_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if current_user.id not in [appointment.student_id, appointment.tutor_id]:
        flash("You are not authorized to cancel this appointment.", "danger")
        return redirect(request.referrer or url_for('index'))

    try:
        recipient_id = appointment.tutor_id if current_user.role == UserRole.STUDENT else appointment.student_id
        subject_name = appointment.subject.name

        # Cancel the appointment and set last_updated_by
        appointment.cancel(current_user.role)
        db.session.delete(appointment)
        db.session.commit()

        # Create an alert for the recipient
        alert = Alert(
            recipient_id=recipient_id,
            catalyst_id=current_user.id,
            appointment_id=appointment.id,
            category='cancel_appointment',
            relevant_date=appointment.booking_date,
            relevant_time=appointment.booking_time,
            subject="Appointment Cancelled",
            message=f"cancelled your appointment together"
        )
        db.session.add(alert)
        db.session.commit()

        flash("The appointment has been successfully canceled.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while canceling the appointment: {str(e)}", "danger")
        return redirect(request.referrer or url_for('index'))

    return redirect(request.referrer or url_for('index'))


@app.route('/api/get_timeslots', methods=['GET'])
def api_get_timeslots():
    tutor_id = request.args.get('tutor_id', type=int)
    selected_date_str = request.args.get('selected_date')

    availabilities = []
    available_times = []
    unavailable_times = []

    if not tutor_id or not selected_date_str:
        return jsonify({'error': 'Missing tutor_id or selected_date'}), 400

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    day_of_week = selected_date.weekday()  # Monday=0

    # Get all availabilities for this tutor on this weekday
    availabilities = Availability.query.filter_by(
        tutor_id=tutor_id,
        day_of_week=day_of_week,
        is_active=True
    ).all()

    # Get all booked times for this tutor on this date
    appointments = db.session.execute(
        db.select(Appointment.booking_time)
        .where(
            Appointment.tutor_id == tutor_id,
            Appointment.booking_date == selected_date
        )
    ).scalars().all()

    booked_times = [appt.time() for appt in appointments]
    booked_set = set(booked_times)

    for availability in availabilities:
        if availability.end_time > availability.start_time:
            # Normal case: same day
            current = datetime.combine(selected_date, availability.start_time)
            end = datetime.combine(selected_date, availability.end_time)
            while current < end:
                slot_time = current.time()
                if slot_time in booked_set:
                    unavailable_times.append(slot_time.strftime('%H:%M'))
                else:
                    available_times.append(slot_time.strftime('%H:%M'))
                current += timedelta(minutes=60)
        else:
            # Overnight: from start_time to end_time, crossing midnight, all on the same day
            current = datetime.combine(selected_date, availability.start_time)
            # End is on the next day at end_time
            end = datetime.combine(selected_date + timedelta(days=1), availability.end_time)
            while current < end:
                # Always print on the start day (selected_date)
                slot_time = (current.time() if current.date() == selected_date else current.time())
                if slot_time in booked_set:
                    unavailable_times.append(slot_time.strftime('%H:%M'))
                else:
                    available_times.append(slot_time.strftime('%H:%M'))
                current += timedelta(minutes=60)

    return jsonify({'available_times': available_times})



#######################
# AVAILABILITY SYSTEM #
#######################


@app.route('/set_availability', methods=['GET', 'POST'])
@login_required
def set_availability():
    if current_user.role != UserRole.TUTOR:
        flash('Only tutors can set availability.', 'danger')
        return redirect(url_for('index'))

    form = AvailabilityForm()
    all_hours = [time(hour, 0) for hour in range(24)]  # Generate hour blocks

    if form.validate_on_submit():
        try:
            availability = current_user.add_availability(
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            db.session.commit()
            flash(f'Availability added successfully!', 'success')
            return redirect(url_for('set_availability'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('set_availability'))

    # Query availabilities properly
    query = sa.select(Availability).where(
        Availability.tutor_id == current_user.id
    ).order_by(
        Availability.day_of_week,
        Availability.start_time
    )
    availabilities = db.session.scalars(query).all()

    return render_template(
        'set_availability.html',
        title='Set Availability',
        form=form,
        availabilities=availabilities,
        all_hours=all_hours  # Pass the hour blocks to the template
    )


@app.route('/delete_availability/<int:availability_id>', methods=['POST'])
@login_required
def delete_availability(availability_id):
    if current_user.role != UserRole.TUTOR:
        flash('Only tutors can manage availability.', 'danger')
        return redirect(url_for('index'))

    query = sa.select(Availability).where(
        Availability.id == availability_id,
        Availability.tutor_id == current_user.id
    )
    availability = db.session.scalar(query)

    if availability is None:
        flash('Availability slot not found.', 'danger')
        return redirect(url_for('set_availability'))

    db.session.delete(availability)
    db.session.commit()
    flash('Availability slot deleted.', 'success')
    return redirect(url_for('set_availability'))



###################
# SUBJECTS SYSTEM #
###################


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


###################
# MESSAGES SYSTEM #
###################

@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count',
                              user.unread_message_count())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('user', username=recipient))
    return render_template('send_message.html', title='Send Message',
                           form=form, recipient=recipient)


@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    alerts_query = current_user.alerts_received.select().order_by(
        Alert.timestamp.desc())
    alerts = db.paginate(alerts_query, page=page,
                           per_page=app.config['POSTS_PER_PAGE'],
                           error_out=False)
    messages = db.paginate(query, page=page,
                           per_page=app.config['POSTS_PER_PAGE'],
                           error_out=False)


    next_url = url_for('messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, alerts=alerts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    
    # Query alerts
    alert_query = current_user.alerts_received.select().where(
        Alert.timestamp > datetime.fromtimestamp(since, timezone.utc)
    ).order_by(Alert.timestamp.asc())
    alerts = db.session.scalars(alert_query)

    # Combine notifications and alerts
    combined = [{
        'type': 'notification',
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications] + [{
        'type': 'alert',
        'message': a.message,
        'subject': a.subject,  # Assuming `subject` is a User
        'timestamp': a.timestamp
    } for a in alerts]

    combined.sort(key=lambda x: x['timestamp'])
    return jsonify(combined)





#########
# DEBUG #
#########


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


@app.route('/test_availability', methods=['GET', 'POST'])
@login_required
def test_availability():
    form = TestAvailabilityForm()

    # Populate the tutor choices dynamically
    form.tutor_id.choices = [(tutor.id, tutor.username) for tutor in User.query.filter_by(role=UserRole.TUTOR).all()]

    availabilities = None
    available_times = []
    unavailable_times = []

    if form.validate_on_submit():
        tutor_id = form.tutor_id.data
        selected_date = form.date.data  # Assume the form includes a date field
        day_of_week = form.day_of_week.data

        # Query the Availability model directly
        availabilities = Availability.query.filter_by(
            tutor_id=tutor_id,
            day_of_week=day_of_week,
            is_active=True
        ).all()

        # Query the Appointment model for booked times on the selected date
        booked_appointments = Appointment.query.filter_by(
            tutor_id=tutor_id,
            booking_date=selected_date
        ).all()

        # Extract booked times
        booked_times = [appointment.booking_time for appointment in booked_appointments]

        # Create a list of all hours in the day
        all_hours = [time(hour, 0) for hour in range(24)]

        # Find available and unavailable times
        for hour in all_hours:
            if any(avail.start_time <= hour < avail.end_time for avail in availabilities) and hour not in booked_times:
                available_times.append(hour)
            else:
                unavailable_times.append(hour)

    return render_template('test_availability.html', form=form, availabilities=availabilities, available_times=available_times, unavailable_times=unavailable_times)



# @app.context_processor
# def inject_user_role():
#     return dict(UserRole=UserRole)