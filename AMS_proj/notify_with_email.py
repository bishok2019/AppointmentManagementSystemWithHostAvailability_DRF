from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

def send_visitor_notification(visitor):
    """Send an email notification to the visitor based on their current status."""
    if not visitor.email:
        return

    status = visitor.status
    from_email = settings.EMAIL_HOST_USER

    if status == 'confirmed':
        subject = "Appointment Confirmed"
        message = f"""Dear {visitor.name},

Your appointment with {visitor.visiting_to.username} has been CONFIRMED.

Confirmed Details:
Date: {visitor.meeting_date}
Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}

Please arrive 10 minutes before your scheduled time.
"""
    elif status == 'cancelled':
        subject = "Appointment Cancelled"
        message = f"""Dear {visitor.name},

Your appointment with {visitor.visiting_to.username} on {visitor.meeting_date} has been CANCELLED.

Original Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}

Please contact us to reschedule.
"""
    elif status == 'checked_in':
        subject = "Checked-In Successfully"
        message = f"""Hello {visitor.name},

Thank you for checking in for your appointment with {visitor.visiting_to.username}.

Current Status: Checked-In
Check-In Time: {timezone.now().strftime('%H:%M')}
"""
    elif status == 'completed':
        subject = "Appointment Completed"
        message = f"""Dear {visitor.name},

Your appointment with {visitor.visiting_to.username} has been marked COMPLETED.

Date: {visitor.meeting_date}
Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}

Thank you for your visit!
"""
    else:
        subject = "Appointment Status Update"
        message = f"""Hello {visitor.name},

Your appointment has been submitted and is: {status.upper()}.

Next Steps: Please wait for host confirmation.
"""

    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=from_email,
        recipient_list=[visitor.email],
        fail_silently=False
    )

def send_host_notification(visitor):
    """Send an email notification to the host when a new visitor appointment is created."""
    host = visitor.visiting_to
    if not getattr(host, 'email', None):
        return

    from_email = settings.EMAIL_HOST_USER
    subject = "New Visitor Appointment Booked"
    message = f"""Dear {host.username},

A new visitor appointment has been booked.

Visitor Details:
Name: {visitor.name}
Company: {visitor.company}
Date: {visitor.meeting_date}
Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
Reason:{visitor.reason}
Status: {visitor.status}
Please check your dashboard for more details.
Visitor Contact:
Phone Number: {visitor.phone_num}
Email: {visitor.email}
Please ensure to check in the visitor upon arrival.
Meeting Duration: {visitor.meeting_duration}
Please be prepared for the meeting.
"""
    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=from_email,
        recipient_list=[host.email],
        fail_silently=False
    )

def send_creation_notifications(visitor):
    """
    For a new appointment, notify both the visitor and the host.
    """
    send_visitor_notification(visitor)
    send_host_notification(visitor)

def send_update_notification(visitor):
    """
    For appointment updates (e.g., rescheduling) only notify the visitor.
    """
    send_visitor_notification(visitor)
