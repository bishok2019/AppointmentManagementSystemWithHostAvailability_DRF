#visitor_app/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from host_app.models import User, HostAvailability
from datetime import datetime, timedelta

# Create your models here.
class Visitor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked-In'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    name = models.CharField(max_length=150)
    phone_num = models.CharField(max_length=15,null=True, blank=True, unique=True)
    email = models.EmailField(null=True, blank=True)
    photo = models.ImageField(upload_to='visitor_photos/',null=True, blank=True)
    company = models.CharField(max_length=150)
    visiting_to = models.ForeignKey(User,on_delete=models.CASCADE,related_name='host')
    meeting_date = models.DateField()
    meeting_start_time = models.TimeField()
    meeting_end_time = models.TimeField()
    reason = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    availability = models.ForeignKey(HostAvailability, on_delete=models.SET_NULL, null=True, blank=True, related_name='visitors')

    def __str__(self):
        return self.name
    
    @property
    def meeting_duration(self):
        return datetime.combine(self.meeting_date, self.meeting_start_time) - datetime.combine(self.meeting_date, self.meeting_end_time)