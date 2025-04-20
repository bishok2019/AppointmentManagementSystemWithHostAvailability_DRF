# # notification/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from visitor_app.models import Visitor
# from host_app.models import HostAvailability
# from .models import Notification
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

# #Every time a Visitor instance is created or updated, this function runs.
# @receiver(post_save, sender=Visitor)
# def send_visitor_update(sender, instance, **kwargs):
#     notification = Notification.objects.create(
#         recipient=instance.visiting_to,
#         notification_type='VISITOR_UPDATE',
#         title=f'Visitor Status Update - {instance.name}',
#         message=f'Visitor {instance.name} status changed to {instance.status}',
#         content_object=instance
#     )
    
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f'notifications_{instance.visiting_to.id}',
#         {
#             'type': 'send_notification',
#             'content': {
#                 'id': notification.id,
#                 'type': notification.notification_type,
#                 'title': notification.title,
#                 'message': notification.message,
#                 'timestamp': notification.created_at.isoformat(),
#                 'related_object': {
#                     'type': 'visitor',
#                     'id': instance.id
#                 }
#             }
#         }
#     )

# @receiver(post_save, sender=HostAvailability)
# def send_host_availability_update(sender, instance, **kwargs):
#     if instance.is_approved:
#         notification = Notification.objects.create(
#             recipient=instance.host,
#             notification_type='HOST_AVAILABILITY',
#             title='Availability Approved' if instance.is_approved else 'Availability Updated',
#             message=f'Your availability for {instance.date} has been approved',
#             content_object=instance
#         )
        
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             f'notifications_{instance.host.id}',
#             {
#                 'type': 'send_notification',
#                 'content': {
#                     'id': notification.id,
#                     'type': notification.notification_type,
#                     'title': notification.title,
#                     'message': notification.message,
#                     'timestamp': notification.created_at.isoformat(),
#                     'related_object': {
#                         'type': 'availability',
#                         'id': instance.id
#                     }
#                 }
#             }
#         )