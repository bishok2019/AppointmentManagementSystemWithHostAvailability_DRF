# notification/notification.py
from django.conf import settings
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.notification_group_name = None  # Initialize here
        try:
            token = self.scope['query_string'].decode().split('token=')[1]
            self.user = await self.get_user(token)
            
            if isinstance(self.user, AnonymousUser):
                await self.close()
                return

            # Only set group name if validation passes
            self.notification_group_name = f'notifications_{self.user.id}'
            
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            await self.accept()

        except Exception as e:
            await self.close(code=4001)  # Proper error code

    async def disconnect(self, close_code):
        # Only attempt to discard if group name exists
        if self.notification_group_name:
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    # Add this method to your NotificationConsumer class
    async def send_notification(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['content']))

    # Also add the missing method to validate user tokens
    @database_sync_to_async
    def get_user(self, token_key):
        try:
            access_token = AccessToken(token_key)
            user_id = access_token['user_id']
            User = get_user_model()
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()