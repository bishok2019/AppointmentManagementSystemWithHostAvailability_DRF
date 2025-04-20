# notification/services.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def create_notification(recipient, notification_type, title, message, content_object=None):
    """
    Create a notification and send it via WebSocket
    """
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        content_object=content_object
    )
    
    channel_layer = get_channel_layer()
    
    # Prepare the notification data for WebSocket
    notification_data = {
        'id': notification.id,
        'type': notification.notification_type,
        'title': notification.title,
        'message': notification.message,
        'timestamp': notification.created_at.isoformat()
    }
    
    # Add related object info if available
    if content_object:
        notification_data['related_object'] = {
            'type': content_object._meta.model_name,
            'id': content_object.id
        }
    
    # Send the notification via WebSocket, This causes Django Channels to look for the method named send_notification in the NotificationConsumer
    async_to_sync(channel_layer.group_send)(
        f'notifications_{recipient.id}',
        {
            'type': 'send_notification',
            'content': notification_data
        }
    )
    
    return notification