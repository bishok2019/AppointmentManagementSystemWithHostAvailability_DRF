from django.db import models
from django.conf import settings

# Create your models here.

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='%(class)s_created_by', null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='%(class)s_updated_by', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField('Permission', related_name='roles')
    
    def __str__(self):
        return self.name

class PermissionCategory(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Permission(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=50, unique=True)
    permissioncategory = models.ForeignKey(PermissionCategory, on_delete=models.CASCADE, related_name='permissions')

    def __str__(self):
        return self.name
