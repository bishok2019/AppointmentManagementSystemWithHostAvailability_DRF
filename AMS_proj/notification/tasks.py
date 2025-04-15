# # notification/tasks.py
# from celery import shared_task
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from .models import Notification
# import logging

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3)
# def send_notification_task(self, recipient_id, notification_id):
#     """
#     Send notification via WebSocket with retry mechanism
#     """
#     try:
#         # Get the notification
#         notification = Notification.objects.get(id=notification_id)
        
#         # Prepare notification data
#         notification_data = {
#             'id': notification.id,
#             'type': notification.notification_type,
#             'title': notification.title,
#             'message': notification.message,
#             'timestamp': notification.created_at.isoformat()
#         }
        
#         # Add related object info if available
#         if notification.content_object:
#             notification_data['related_object'] = {
#                 'type': notification.content_object._meta.model_name,
#                 'id': notification.content_object.id
#             }
        
#         # Send via WebSocket
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             f'notifications_{recipient_id}',
#             {
#                 'type': 'send_notification',
#                 'content': notification_data
#             }
#         )
        
#         return f"Notification {notification_id} sent to user {recipient_id}"
    
#     except Exception as e:
#         logger.error(f"Failed to send notification {notification_id}: {str(e)}")
#         # Retry with exponential backoff
#         retry_countdown = 2 ** self.request.retries
#         raise self.retry(exc=e, countdown=retry_countdown)

# # Update services.py to use the task
# # notification/services.py
# from .tasks import send_notification_task

# def create_notification(recipient, notification_type, title, message, content_object=None):
#     """
#     Create a notification and queue it for delivery
#     """
#     notification = Notification.objects.create(
#         recipient=recipient,
#         notification_type=notification_type,
#         title=title,
#         message=message,
#         content_object=content_object
#     )
    
#     # Queue the notification for delivery
#     send_notification_task.delay(recipient.id, notification.id)
    
#     return notification