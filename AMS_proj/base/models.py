# base/models.py
from django.db import models
from django.conf import settings
from .middleware import get_current_user  # Import from middleware in the same base dir

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='%(class)s_created_by', null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='%(class)s_updated_by', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and not user.is_anonymous:
            if not self.pk:  # Object is being created
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        abstract = True  # Marks this as a reusable abstract base class