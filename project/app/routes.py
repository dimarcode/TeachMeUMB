from datetime import datetime, timezone, time, timedelta, date
from urllib.parse import urlsplit
from pytz import timezone as pytz_timezone
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_moment import moment
import sqlalchemy as sa
from sqlalchemy import select
from app import app, db, mail
from app.forms import LoginForm, RegistrationForm, EditProfileForm, UserSubjectForm, \
BookAppointmentForm, UpdateAppointmentForm, RequestClassForm, MessageForm, ResetPasswordRequestForm, \
ResetPasswordForm, AvailabilityForm, TestAvailabilityForm, BeginAppointmentForm, ReviewAppointmentForm
from app.models import User, UserRole, Subject, Appointment, RequestedSubject, Message, \
Notification, Alert, Availability, Review
from app.email import send_password_reset_email
from app.utils import save_picture


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

    # Homepage message if student has no subjects or tutor has no availability
    homepage_messages = []

    if current_user.role == UserRole.STUDENT and not current_user.my_subjects:
        homepage_messages.append({
            'type': 'warning',
            'link_text': 'Choose the classes you are taking this semester',
            'link_url': url_for('add_subject')
        })

    elif current_user.role == UserRole.TUTOR:
        has_availability = db.session.query(Availability).filter_by(
            tutor_id=current_user.id,
            is_active=True
        ).first()
        if not has_availability:
            homepage_messages.append({
                'type': 'warning',
                'link_text': 'Set your availability schedule',
                'link_url': url_for('set_availability')
            })

        if not current_user.my_subjects:
            homepage_messages.append({
                'type': 'warning',
                'link_text': 'Add the classes you can tutor in',
                'link_url': url_for('add_subject')
            })

    def get_appointments_needing_review(user):
        # Appointments where user is a participant, status is 'needs_review', and user hasn't reviewed yet
        appointments = (
            db.session.scalars(
                select(Appointment)
                .where(
                    ( (Appointment.student_id == user.id) | (Appointment.tutor_id == user.id) ),
                    Appointment.status == 'needs_review'
                )
            ).all()
        )
        # Filter out those already reviewed by this user
        needing_review = []
        for appt in appointments:
            # Query for a review by this user for this appointment
            review_exists = db.session.scalar(
                select(Review).where(
                    Review.appointment_id == appt.id,
                    Review.author_id == user.id
                )
            )
            if not review_exists:
                needing_review.append(appt)
        return needing_review

    # In your route:
    appointments_needing_review = get_appointments_needing_review(current_user)

    return render_template(
        'index.html',
        pending_needs_approval=pending_needs_approval,
        pending_waiting_for_other=pending_waiting_for_other,
        confirmed_appointments=confirmed_appointments,
        completed_appointments=completed_appointments,
        requested_subjects=requested_subjects,
        form=form,
        UserRole=UserRole,
        homepage_messages=homepage_messages,
        appointments_needing_review=appointments_needing_review
    )



@app.route('/api/events')
@login_required
def api_events():
    appointments = Appointment.query.filter(
        ((Appointment.student_id == current_user.id) | (Appointment.tutor_id == current_user.id)) &
        (~Appointment.status.in_(['needs_review', 'completed']))
    ).all()

    eastern = pytz_timezone("America/New_York")

    events = []
    for appointment in appointments:
        event = {
            'id': appointment.id,
            'title': f"{appointment.subject.name} with {appointment.tutor.username if current_user.role == UserRole.STUDENT else appointment.student.username}",
            'start': appointment.booking_time.isoformat(),
            'end': (appointment.booking_time + timedelta(hours=1)).isoformat(),
            'status': appointment.status,
            'url': f"/appointment/{appointment.id}",
            'description': f"Subject: {appointment.subject.name}, Status: {appointment.status}",
            'display_date': appointment.booking_date.strftime('%B %d, %Y'),
            'display_time': appointment.booking_time.astimezone(eastern).strftime('%I:%M %p')
        }
        events.append(event)

    return jsonify(events)



################
# USER PROFILE #
################


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = BookAppointmentForm()  # Create an instance of the form
    my_subject_ids = [subject.id for subject in current_user.my_subjects]

    requested_subjects = (
        db.session.query(Subject)
        .join(RequestedSubject)
        .filter(
            RequestedSubject.student_id == current_user.id,
            Subject.id.in_(my_subject_ids)
        )
        .all()
    )
    return render_template('user.html', user=user, form=form, requested_subjects=requested_subjects, UserRole = UserRole)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_picture = picture_file
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.profile_picture.data = current_user.profile_picture
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)



#######################
# APPOINTMENTS SYSTEM #
#######################


@app.route('/explore')
@login_required
def explore():
    form = BookAppointmentForm()

    if current_user.role == UserRole.STUDENT:
        # Get selected subject IDs from the checkbox form
        subject_ids = request.args.getlist('subject_ids', type=int)

        if subject_ids:
            # Show tutors who teach any of the selected subjects
            tutors = User.query.filter(
                User.role == UserRole.TUTOR,
                User.id != current_user.id,
                User.my_subjects.any(Subject.id.in_(subject_ids))
            ).all()
        else:
            # Show tutors who share any subject with the student
            tutors = User.query.filter(
                User.role == UserRole.TUTOR,
                User.id != current_user.id,
                User.my_subjects.any(Subject.id.in_([s.id for s in current_user.my_subjects]))
            ).all()


        weeks_ahead = 4
        filtered_tutors = []
        debug_info = []  # <-- Add this

        for tutor in tutors:
            availabilities = Availability.query.filter_by(
                tutor_id=tutor.id,
                is_active=True
            ).all()

            tutor_debug = {
                'tutor': tutor,
                'availabilities': availabilities,
                'filtered_out': False,
                'reason': '',
                'booked': []
            }

            has_open_slot = False

            def generate_slots(start, end):
                slots = []
                current = datetime.combine(date.today(), start)
                # If overnight, end is on the next day
                if end <= start:
                    end_dt = datetime.combine(date.today() + timedelta(days=1), end)
                else:
                    end_dt = datetime.combine(date.today(), end)
                while current < end_dt:
                    slots.append(current.time())
                    current += timedelta(hours=1)
                return slots

            # ... inside your availability loop ...
            for availability in availabilities:
                for week_offset in range(weeks_ahead):
                    days_ahead = (availability.day_of_week - date.today().weekday()) % 7 + 7 * week_offset
                    check_date = date.today() + timedelta(days=days_ahead)

                    booked_appointments = Appointment.query.filter_by(
                        tutor_id=tutor.id,
                        booking_date=check_date
                    ).with_entities(Appointment.booking_time).all()

                    tutor_debug['booked'].append({
                        'date': check_date,
                        'booked_times': [bt.booking_time for bt in booked_appointments]
                    })

                    booked_times = {bt.booking_time.time() for bt in booked_appointments}

                    # Generate all slots for this availability
                    slots = generate_slots(availability.start_time, availability.end_time)
                    for slot in slots:
                        if slot not in booked_times:
                            has_open_slot = True
                            break
                    if has_open_slot:
                        break
                if has_open_slot:
                    break

            if has_open_slot:
                filtered_tutors.append(tutor)
            else:
                tutor_debug['filtered_out'] = True
                tutor_debug['reason'] = "No open slots in the next 4 weeks"
                debug_info.append(tutor_debug)


        return render_template(
            'explore.html',
            title='Explore',
            tutors=filtered_tutors,
            form=form,
            UserRole=UserRole,
            debug_info=debug_info  # <-- Pass the debug info to the template
        )

    elif current_user.role == UserRole.TUTOR:
        # Show requested classes for tutors
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
            UserRole=UserRole
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
            location_id = form.location_id.data  # Expecting this is the location's ID

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
                last_updated_by=current_user.role,
                location_id=location_id  # <-- Use location_id here
            )

            db.session.add(appointment)
            db.session.commit()

            # Create an alert for the tutor
            alert = Alert(
                
                category='book_appointment',
                headline="New Appointment Booked",
                message=f"booked an appointment with you for tutoring in {subject.name}.",
                relevant_date=booking_date,
                relevant_time=booking_datetime,
                subject_name=subject.name,

                recipient_id=tutor.id,
                catalyst_id=current_user.id,
                appointment_id=appointment.id,
                location_id=location_id,
               # subject=subject.id,
            )

            db.session.add(alert)
            db.session.commit()

            flash(f"Appointment booked with {tutor.username} for {subject.name}. They have been sent an alert.", "success")
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error booking appointment: {str(e)}", "danger")

    return render_template('book_appointment.html', form=form, tutor=tutor)


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

        # Determine recipient (the other party)
        recipient_id = appointment.student_id if current_user.role == UserRole.TUTOR else appointment.tutor_id

        # Create an alert for the recipient
        alert = Alert(
            category='book_appointment',
            headline="Appointment Changes Approved",
            message=(f"booked an appointment with you for {appointment.subject.name}"),
            relevant_date=appointment.booking_date,
            relevant_time=appointment.booking_time,
            subject_name=appointment.subject.name,
            
            recipient_id=recipient_id,
            catalyst_id=current_user.id,
            appointment_id=appointment.id,
            location_id=appointment.location_id,  # Use the location ID from the appointment
        )
        db.session.add(alert)
        db.session.commit()

        flash(f"Appointment {appointment.id} has been confirmed.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while confirming the appointment: {str(e)}", "danger")

    return redirect(request.referrer or url_for('index'))


@app.route('/appointment_update/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def appointment_update(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    tutor_id = request.args.get('tutor_id', type=int)

    if not tutor_id:
        flash("Invalid tutor selected.", "danger")
        return redirect(url_for('explore'))

    tutor = User.query.get_or_404(tutor_id)

    form = UpdateAppointmentForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            tutor = User.query.get_or_404(tutor_id)
            booking_date = form.booking_date.data
            booking_time = form.booking_time.data
            location_id = form.location_id.data
            directions = form.directions.data

            booking_datetime = datetime.combine(
                booking_date,
                booking_time,
                tzinfo=timezone.utc
            )

            # Update the appointment
            appointment.update(
                booking_date=booking_date,
                booking_time=booking_datetime,
                location_id=location_id,
                directions=directions,
                user_role=current_user.role,  # Set the role of the user updating the appointment
            )

            db.session.commit()

            recipient_id = appointment.tutor_id if current_user.role == UserRole.STUDENT else appointment.student_id
            recipient = User.query.get(recipient_id)
            subject = Subject.query.get(appointment.subject_id)
            # Create an alert for the other party
            alert = Alert(
                category='update_appointment',
                headline="Appointment Details Updated",
                message=f"Updated the details of your tutoring session for {subject.name}",
                relevant_date=booking_date,
                relevant_time=booking_datetime,
                subject_name=appointment.subject.name,
                recipient_id=recipient_id,
                catalyst_id=current_user.id,
                appointment_id=appointment.id,
                location_id=location_id,
            )

            db.session.add(alert)
            db.session.commit()

            flash(f"Your appointment with {recipient.username} for {subject.name} has been updated. They have been sent an alert.", "success")
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating appointment: {str(e)}", "danger")

    return render_template('appointment_update.html', form=form, appointment=appointment, tutor=tutor, tutor_id=tutor_id)


@app.route('/remove_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def remove_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if current_user.id not in [appointment.student_id, appointment.tutor_id]:
        flash("You are not authorized to cancel this appointment.", "danger")
        return redirect(request.referrer or url_for('index'))

    try:
        recipient_id = appointment.tutor_id if current_user.role == UserRole.STUDENT else appointment.student_id

        # Create an alert for the recipient
        alert = Alert(
            category='cancel_appointment',
            headline="Appointment Cancelled",
            message=f"cancelled your appointment together",
            relevant_date=appointment.booking_date,
            relevant_time=appointment.booking_time,
            subject_name=appointment.subject.name,
            
            recipient_id=recipient_id,
            catalyst_id=current_user.id,
            appointment_id=appointment.id,
            location_id=appointment.location_id,
        )
        db.session.add(alert)
        db.session.commit()

        appointment.cancel(current_user.role)
        db.session.delete(appointment)
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


@app.route('/appointment/<int:appointment_id>/begin', methods=['GET', 'POST'])
@login_required
def begin_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role != UserRole.TUTOR or appointment.tutor_id != current_user.id:
        flash("Only the assigned tutor can begin this appointment.", "danger")
        return redirect(url_for('index'))
    form = BeginAppointmentForm()
    if form.validate_on_submit():
        appointment.actual_start_time = datetime.combine(appointment.booking_date, form.start_time.data)
        appointment.actual_end_time = datetime.combine(appointment.booking_date, form.end_time.data)
        appointment.complete(current_user.role)  # Set status to 'needs_review'
        db.session.commit()
        return redirect(url_for('review_appointment', appointment_id=appointment.id))
    return render_template('begin_appointment.html', form=form, appointment=appointment)


@app.route('/appointment/<int:appointment_id>/review', methods=['GET', 'POST'])
@login_required
def review_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.id not in [appointment.student_id, appointment.tutor_id]:
        flash("You are not authorized to review this appointment.", "danger")
        return redirect(url_for('index'))
    already_reviewed = db.session.scalar(
        select(Review).where(
            Review.appointment_id == appointment.id,
            Review.author_id == current_user.id
        )
    ) is not None
    if already_reviewed:
        flash("You have already reviewed this appointment.", "info")
        return redirect(url_for('index'))
    form = ReviewAppointmentForm()
    if form.validate_on_submit():
        recipient_id = appointment.tutor_id if current_user.id == appointment.student_id else appointment.student_id
        review = Review(
            appointment_id=appointment.id,
            author_id=current_user.id,
            recipient_id=recipient_id,
            stars=form.stars.data,
            text=form.text.data
        )
        db.session.add(review)
        # Only finalize if both have reviewed
        if appointment.both_reviewed():
            appointment.finalize(current_user.role)
        db.session.commit()
        flash("Thank you for your review!", "success")
        return redirect(url_for('index'))
    return render_template('review_appointment.html', form=form, appointment=appointment)



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

    # Try to get subject_id from either POST form or WTForms
    subject_id = None
    if request.method == 'POST':
        subject_id = request.form.get('subject_id') or form.subject.data

    if subject_id:
        subject = Subject.query.get(subject_id)
        if subject:
            if subject in current_user.my_subjects:
                flash(f'You already have {subject.name} added to your profile.', 'warning')
            else:
                current_user.my_subjects.append(subject)
                db.session.commit()
                flash(f'{subject.name} has been added to your profile.', 'success')

                # ALERT LOGIC: Tutor adds a subject that matches a requested subject
                if current_user.role == UserRole.TUTOR:
                    requested_students = db.session.query(RequestedSubject).filter_by(subject_id=subject.id).all()
                    for req in requested_students:
                        alert = Alert(
                            category='subject_available',
                            headline="Subject Now Available",
                            message=f"has added the subject you requested to their available classes. \
                            You may now book an appointment with them!",
                            relevant_date=datetime.now(timezone.utc).date(),
                            relevant_time=datetime.now(timezone.utc),
                            subject_name=subject.name,
                            recipient_id=req.student_id,
                            catalyst_id=current_user.id,
                        )
                        db.session.add(alert)
                    db.session.commit()
        else:
            flash('Invalid subject.', 'danger')
        # Redirect back to where the request came from, or fallback
        return redirect(request.referrer or url_for('add_subject'))

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


@app.route('/remove_alert/<int:alert_id>')
@login_required
def remove_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    if alert.recipient_id == current_user.id:
        alert.remove()
        flash('Alert removed successfully.', 'success')
    else:
        flash('You are not authorized to remove this alert.', 'danger')
    return redirect(request.referrer or url_for('index'))


@app.route('/archive_alert/<int:alert_id>')
@login_required
def archive_alert(alert_id):  # <-- Unique function name
    alert = Alert.query.get_or_404(alert_id)
    if alert.recipient_id == current_user.id:
        alert.archive()
        flash('Alert archived successfully.', 'success')
    else:
        flash('You are not authorized to archive this alert.', 'danger')
    return redirect(request.referrer or url_for('index'))


@app.route('/reset_alert/<int:alert_id>')
@login_required
def reset_alert(alert_id):  # <-- Unique function name
    alert = Alert.query.get_or_404(alert_id)
    if alert.recipient_id == current_user.id:
        alert.reset()
        flash('Alert archived successfully.', 'success')
    else:
        flash('You are not authorized to reset this alert.', 'danger')
    return redirect(request.referrer or url_for('index'))


@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    
    active_alerts_query = current_user.alerts_received.select().where(
        Alert.status == "active").order_by(
            Alert.timestamp.desc())

    archived_alerts_query = current_user.alerts_received.select().where(
        Alert.status == "archived").order_by(
            Alert.timestamp.desc())
    
    active_alerts = db.paginate(active_alerts_query, page=page,
                           per_page=app.config['POSTS_PER_PAGE'],
                           error_out=False)
    
    archived_alerts = db.paginate(archived_alerts_query, page=page,
                           per_page=app.config['POSTS_PER_PAGE'],
                           error_out=False)
    
    messages = db.paginate(query, page=page,
                           per_page=app.config['POSTS_PER_PAGE'],
                           error_out=False)

    next_url = url_for('messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, active_alerts=active_alerts.items, 
                           archived_alerts=archived_alerts.items, next_url=next_url, prev_url=prev_url)


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
        'headline': a.headline,  # Assuming `subject` is a User
        'timestamp': a.timestamp
    } for a in alerts]

    def to_datetime(ts):
        if isinstance(ts, float):
            return datetime.fromtimestamp(ts, timezone.utc)
        return ts

    combined.sort(key=lambda x: to_datetime(x['timestamp']))





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