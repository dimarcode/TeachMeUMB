from calendar import HTMLCalendar
from flask_sqlalchemy import SQLAlchemy
from app.models import Appointment  # adjust this import to your project structure
from sqlalchemy import extract
from markupsafe import Markup

class AppointmentCalendar(HTMLCalendar):
    def __init__(self, year, month):
        super().__init__()
        self.year = year
        self.month = month

    def formatday(self, day, appointments):
        day_appointments = [
            appt for appt in appointments if appt.booking_date.day == day
        ]
        appointments_html = ''.join(f"<li>{appt.get_html_url()}</li>" for appt in day_appointments)
        return f"<td><span>{day}</span><ul>{appointments_html}</ul></td>" if day != 0 else "<td></td>"

    def formatweek(self, theweek, appointments):
        week_html = ''.join(self.formatday(d, appointments) for d, _ in theweek)
        return f"<tr>{week_html}</tr>"

    def formatmonth(self, withyear=True):
        appointments = Appointment.query.filter(
            extract('year', Appointment.booking_date) == self.year,
            extract('month', Appointment.booking_date) == self.month
        ).all()

        cal_html = f'<table class="table table-bordered calendar">\n'
        cal_html += self.formatmonthname(self.year, self.month, withyear=withyear) + '\n'
        cal_html += self.formatweekheader() + '\n'

        for week in self.monthdays2calendar(self.year, self.month):
            cal_html += self.formatweek(week, appointments) + '\n'

        cal_html += '</table>'
        return Markup(cal_html)  # Ensures safe rendering in templates