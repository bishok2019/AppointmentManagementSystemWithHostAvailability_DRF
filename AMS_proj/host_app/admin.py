from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, HostAvailability
from role_app.models import Role
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Roles', {'fields': ('role',)}),
        ('Status', {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

# Register with the custom UserAdmin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(HostAvailability)
