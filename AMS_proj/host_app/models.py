#host_app/models.py
from django.db import models
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from django.utils import timezone
from django.conf import settings
from role_app.models import Role
from django.core.exceptions import ValidationError

# from visitor_app.models import Visitor
# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    dep_code = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.ManyToManyField(Role, related_name='role', blank=True)
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class HostAvailability(models.Model):
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_approved = models.BooleanField(default=False)
    is_booked = models.BooleanField(default=False)
    # visitor = models.ForeignKey('visitor_app.Visitor', on_delete=models.SET_NULL, null=True, blank=True)
    
    @classmethod
    def find_available_coverage(cls, host, date, start_time, end_time,exclude_slot=None):
        slots = cls.objects.filter(
            host=host,
            date=date,
            # is_booked=False,
            is_approved=True,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).order_by('start_time').exclude(id=exclude_slot.id if exclude_slot else None)

        coverage = []
        current_start = start_time
        for slot in slots:
            # Include slots that contain the current_start, even if they start before it
            if slot.end_time > current_start:
                coverage_end = min(slot.end_time, end_time)
                coverage.append({
                    'slot': slot,
                    'start': max(slot.start_time, current_start),
                    'end': coverage_end
                })
                current_start = coverage_end
                if current_start >= end_time:
                    return coverage
        return None if not coverage else coverage