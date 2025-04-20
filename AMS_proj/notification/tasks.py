# notification/tasks.py
from datetime import datetime, timedelta
from django.utils import timezone
from notification.services import create_notification
from visitor_app.models import Visitor
from celery import shared_task

@shared_task

def notify_hosts_of_upcoming_appointments():
    """
    Check for appointments scheduled for today or tomorrow and notify hosts
    This function should be run daily through a scheduled task
    """
    now = timezone.localtime(timezone.now())
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # Day-before reminders for tomorrow's appointment
    day_before_task = Visitor.objects.filter(
        meeting_date = tomorrow,
        status = 'confirmed',
        reminder_for_a_day_before_meeting_sent = False
    )
    
   # Day-of reminders for today's appointments
    day_of_task = Visitor.objects.filter(
        meeting_date=today,
        status='confirmed',
        reminder_for_a_day_of_meeting_sent=False
    )

     # 5-minute reminders
    five_minute_window = now + timedelta(minutes=5)
    five_minute_before = Visitor.objects.filter(
        meeting_date=today,
        meeting_start_time__lte=five_minute_window.time(),
        meeting_start_time__gte=now.time(),
        status='confirmed',
        reminder_for_a_five_minute_before_meeting_sent=False
    )
    # Process day-before reminders
    for appointment in day_before_task:
        create_notification(
            recipient=appointment.visiting_to,
            notification_type='APPOINTMENT_REMINDER',
            title='Appointment Tomorrow',
            message=f'You have an appointment with {appointment.name} tomorrow at {appointment.meeting_start_time.strftime("%H:%M")}',
            content_object=appointment
        )
        appointment.reminder_for_a_day_before_meeting_sent = True
        appointment.save()
    
    # Process day-of reminders
    for appointment in day_of_task:
        create_notification(
            recipient=appointment.visiting_to,
            notification_type='APPOINTMENT_REMINDER',
            title='Appointment Today',
            message=f'You have an appointment with {appointment.name} today at {appointment.meeting_start_time.strftime("%H:%M")}',
            content_object=appointment
        )
        appointment.reminder_for_a_day_of_meeting_sent = True
        appointment.save()
    
     # Process 5-minute reminders
    for appointment in five_minute_before:
        create_notification(
            recipient=appointment.visiting_to,
            notification_type='APPOINTMENT_REMINDER',
            title='Appointment Starting Soon',
            message=f'Your appointment with {appointment.name} starts in 5 minutes!',
            content_object=appointment
        )
        appointment.reminder_for_a_five_minute_before_meeting_sent = True
        appointment.save()