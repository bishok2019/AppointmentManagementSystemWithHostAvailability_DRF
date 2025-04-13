# notification/routing.py
from django.urls import re_path
from . import notification

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', notification.NotificationConsumer.as_asgi()),
]