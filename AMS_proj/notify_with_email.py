# from django.core.mail import send_mail
# from django.utils import timezone
# from django.conf import settings

# def send_visitor_notification(visitor):
#     """Send an email notification to the visitor based on their current status."""
#     if not visitor.email:
#         return

#     status = visitor.status
#     from_email = settings.EMAIL_HOST_USER

#     if status == 'confirmed':
#         subject = "Appointment Confirmed"
#         message = f"""Dear {visitor.name},

# Your appointment with {visitor.visiting_to.username} has been CONFIRMED.

# Confirmed Details:
# Date: {visitor.meeting_date}
# Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}

# Please arrive 10 minutes before your scheduled time.
# """
#     elif status == 'cancelled':
#         subject = "Appointment Cancelled"
#         message = f"""Dear {visitor.name},

# Your appointment with {visitor.visiting_to.username} on {visitor.meeting_date} has been CANCELLED.

# Original Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}

# Please contact us to reschedule.
# """
#     elif status == 'checked_in':
#         subject = "Checked-In Successfully"
#         message = f"""Hello {visitor.name},

# Thank you for checking in for your appointment with {visitor.visiting_to.username}.

# Current Status: Checked-In
# Check-In Time: {timezone.now().strftime('%H:%M')}
# """
#     elif status == 'completed':
#         subject = "Appointment Completed"
#         message = f"""Dear {visitor.name},

# Your appointment with {visitor.visiting_to.username} has been marked COMPLETED.

# Date: {visitor.meeting_date}
# Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}

# Thank you for your visit!
# """
#     else:
#         subject = "Appointment Status Update"
#         message = f"""Hello {visitor.name},

# Your appointment has been submitted and is: {status.upper()}.

# Next Steps: Please wait for host confirmation.
# """

#     send_mail(
#         subject=subject,
#         message=message.strip(),
#         from_email=from_email,
#         recipient_list=[visitor.email],
#         fail_silently=False
#     )

# def send_host_notification(visitor):
#     """Send an email notification to the host when a new visitor appointment is created."""
#     host = visitor.visiting_to
#     if not getattr(host, 'email', None):
#         return

#     from_email = settings.EMAIL_HOST_USER
#     subject = "New Visitor Appointment Booked"
#     message = f"""Dear {host.username},

# A new visitor appointment has been booked.

# Visitor Details:
# Name: {visitor.name}
# Company: {visitor.company}
# Date: {visitor.meeting_date}
# Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
# Reason:{visitor.reason}
# Status: {visitor.status}
# Please check your dashboard for more details.
# Visitor Contact:
# Phone Number: {visitor.phone_num}
# Email: {visitor.email}
# Please ensure to check in the visitor upon arrival.
# Meeting Duration: {visitor.meeting_duration}
# Please be prepared for the meeting.
# """
#     send_mail(
#         subject=subject,
#         message=message.strip(),
#         from_email=from_email,
#         recipient_list=[host.email],
#         fail_silently=False
#     )

# def send_creation_notifications(visitor):
#     """
#     For a new appointment, notify both the visitor and the host.
#     """
#     send_visitor_notification(visitor)
#     send_host_notification(visitor)

# def send_update_notification(visitor):
#     """
#     For appointment updates (e.g., rescheduling) only notify the visitor.
#     """
#     send_visitor_notification(visitor)


from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def send_visitor_notification(visitor, change_type=None, old_host=None):
    """Send visitor notifications based on status or changes"""
    if not visitor.email:
        return
    
    status = visitor.status
    host = visitor.visiting_to
    from_email = settings.EMAIL_HOST_USER
    
    if change_type == "host_change" and old_host:
        subject = "Appointment Host Changed"
        message = f"""Dear {visitor.name},
        Your appointment has been transferred to a new host.

        Previous Host: {old_host.username}
        New Host: {host.username}
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status:{visitor.status}

        Please note this change for your visit.
        """
    elif change_type == "creation":  # creation case
        subject = "Appointment Booked"
        message = f"""Hello {visitor.name},
        Your appointment details:
        Host: {host.username}
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status: {status}"""
        
    else:
        if status == 'confirmed':
            subject = "Appointment Confirmed"
            message = f"""Dear {visitor.name},
            Your appointment with {host.username} has been CONFIRMED.
            Date: {visitor.meeting_date}
            Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
            Status:{visitor.status}

        Please arrive 10 minutes early.
        """
        elif status == 'cancelled':
            subject = "Appointment Cancelled"
            message = f"""Dear {visitor.name},
            Your appointment with {host.username} on {visitor.meeting_date} has been CANCELLED.
            Original Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
            """
        elif status == 'checked_in':
            subject = "Checked-In Successfully"
            message = f"""Hello {visitor.name},
            You've checked in for your appointment with {host.username}.
            Check-In Time: {timezone.now().strftime('%H:%M')}
            """
        elif status == 'completed':
            subject = "Appointment Completed"
            message = f"""Dear {visitor.name},
            Your appointment with {host.username} has been COMPLETED.
            Thank you for visiting!
            """
        else:  # For pending or other status
            subject = "Appointment Booked"
            message = f"""Hello {visitor.name},
            Your appointment details:
            Host: {host.username}
            Date: {visitor.meeting_date}
            Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
            Status:{visitor.status}
            """
        
    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=from_email,
        recipient_list=[visitor.email],
        fail_silently=False
    )

def send_update_notification(visitor, old_host=None):
    """Send notifications based on update type"""
    if old_host:
        
        send_visitor_notification(visitor, change_type="host_change", old_host=old_host)
        #Send email to new host
        send_host_notification(visitor, notification_type="host_change", old_host=old_host)
        #Send email to old host
        send_host_notification(visitor, notification_type="removed", old_host=old_host)
    else:        
        # Always notify visitor of changes
        send_visitor_notification(visitor)
        
        # Notify host based on status
        if visitor.status == 'confirmed':
            send_host_notification(visitor, "update")
        elif visitor.status == 'cancelled':
            send_host_notification(visitor, "cancellation")

# Send_host_notification for all notification scenarios
def send_host_notification(visitor, notification_type="new", old_host=None):
    """Send host notifications for various scenarios"""
    host = visitor.visiting_to
    from_email = settings.EMAIL_HOST_USER
    
    # Handle notification-specific content
    if notification_type == "new":
        # NEW APPOINTMENT notification to host
        if not getattr(host, 'email', None):
            return
        subject = "New Appointment Booked"
        message = f"""Dear {host.username},
        A new appointment has been scheduled:
        Visitor: {visitor.name} ({visitor.company})
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}"""
        recipient = host.email

    elif notification_type == "update":
        # UPDATE notification to host
        if not getattr(host, 'email', None):
            return
        subject = "Appointment Updated"
        message = f"""Dear {host.username},
        An appointment has been modified:
        Visitor: {visitor.name}
        Meeting Date: {visitor.meeting_date}
        Meeting Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status:{visitor.status}"""
        
        recipient = host.email
        
    elif notification_type == "cancellation":
        # CANCELLATION notification to host
        if not getattr(host, 'email', None):
            return
        subject = "Appointment Cancelled"
        message = f"""Dear {host.username},
        An appointment has been cancelled:
        Visitor: {visitor.name}
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status:{visitor.status}
        """
        recipient = host.email

    elif notification_type == "host_change":
        # HOST CHANGE notification to new host
        if not getattr(host, 'email', None):
            return
        subject = "New Appointment Transferred to You"
        message = f"""Dear {host.username},
        An appointment has been transferred to you from {old_host.username}:
        Visitor: {visitor.name} ({visitor.company})
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status:{visitor.status}"""
        recipient = host.email

    elif notification_type == "removed":
        # REMOVED notification to old host
        if not old_host or not getattr(old_host, 'email', None):
            return
        subject = "Appointment Reassigned"
        message = f"""Dear {old_host.username},
        The appointment with {visitor.name} on {visitor.meeting_date} has been reassigned to another host."""
        recipient = old_host.email
    else:
        # Default case
        if not getattr(host, 'email', None):
            return
        recipient = host.email
    
    # Send the email
    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=from_email,
        recipient_list=[recipient],
        fail_silently=False
    )

# Function to ensure both visitor and host are notified on creation
def send_creation_notifications(visitor):
    """Notify both visitor and host on appointment creation"""
    send_visitor_notification(visitor, change_type="creation")  # Notify visitor
    send_host_notification(visitor, "new")  # Notify host