# AMS_proj/celery.py
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AMS_proj.settings')

app = Celery('AMS_proj')

# Configure Celery using Django settings (CELERY_* variables)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Add explicitly to ensure it's using Redis
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()