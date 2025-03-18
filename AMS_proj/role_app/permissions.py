from rest_framework.permissions import BasePermission
from.models import Permission
class IsSuperUser(BasePermission):
    """
    To check user is superuser or not
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class HasPermission(BasePermission):
    """
    Custom permission class to check if a user has the required permission.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Extract the required permission from the view
        required_permission = getattr(view, 'required_permission', None)
        # If no specific permission is required, allow access
        if not required_permission:
            return True
        user_roles = request.user.role.all()
        user_permissions=set()
        for role in user_roles:
        # Checking if user has the required permission
            user_permissions = set(Permission.objects.filter(roles__in=user_roles).values_list('code', flat=True))
            # Incorrect: This does not work because `role` is a Many-to-Many relationship.
            # It would work only if `role` were a ForeignKey, where a single role is linked to the user.
            # Since a user can have multiple roles, we must first fetch all roles before accessing their permissions.
            # user_permissions = set(request.user.role.permissions.values_list('code', flat=True))
        return required_permission in user_permissions
        