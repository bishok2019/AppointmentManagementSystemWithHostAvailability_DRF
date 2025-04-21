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
        Status: {visitor.status}

        Please note this change for your visit.
        """
        if status == 'pending':
            message += "\nPlease wait for your new host to confirm the appointment."
            
    elif change_type == "creation":  # creation case
        subject = "Appointment Booked"
        message = f"""Hello {visitor.name},
        Your appointment details:
        Host: {host.username}
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status: {status}"""
        
        if status == 'pending':
            message += "\nPlease wait for host confirmation."
    
    elif change_type == "update":  # Add an explicit update case
        subject = "Appointment Updated"
        message = f"""Dear {visitor.name},
        Your appointment details have been updated:
        
        Host: {host.username}
        Date: {visitor.meeting_date}
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status: {status}
        """
        
        # Add status-specific messages
        if status == 'pending':
            message += "\nPlease wait for host confirmation."
        elif status == 'confirmed':
            message += "\nYour appointment has been confirmed. Please arrive 10 minutes early."
        elif status == 'cancelled':
            message += "\nThis appointment has been cancelled."
        
    else:
        if status == 'confirmed':
            subject = "Appointment Confirmed"
            message = f"""Dear {visitor.name},
            Your appointment with {host.username} has been CONFIRMED.
            Date: {visitor.meeting_date}
            Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
            Status: {visitor.status}

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
            Status: {visitor.status}
            
            Please wait for host confirmation.
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
        # Always notify visitor of changes with an explicit update type
        send_visitor_notification(visitor, change_type="update")
        
        # Notify host based on status
        if visitor.status == 'confirmed':
            send_host_notification(visitor, "update")
        elif visitor.status == 'cancelled':
            send_host_notification(visitor, "cancellation")
        else:
            send_host_notification(visitor, "update")

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
        Time: {visitor.meeting_start_time} to {visitor.meeting_end_time}
        Status: {visitor.status}
        
        This appointment requires your confirmation."""
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
        Status: {visitor.status}"""
        
        if visitor.status == 'pending':
            message += "\n\nThis appointment requires your confirmation."
        
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
        Status: {visitor.status}
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
        Status: {visitor.status}"""
        
        if visitor.status == 'pending':
            message += "\n\nThis appointment requires your confirmation."
            
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