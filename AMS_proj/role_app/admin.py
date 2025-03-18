from django.contrib import admin
from .models import Role, Permission, PermissionCategory
# Register your models here.

admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(PermissionCategory)