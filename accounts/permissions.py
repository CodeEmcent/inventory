from rest_framework.permissions import BasePermission

class IsAdminOrStaffOrReadOnly(BasePermission):
    """
    Custom permission to allow only admins to edit or delete, 
    but everyone can read.
    """
    def has_permission(self, request, view):
        # Allow all users to perform GET, HEAD, or OPTIONS requests (read-only).
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Allow only authenticated users with 'admin' role to perform other requests.
        return request.user.is_authenticated and request.user.role in ('admin', 'staff')

class IsSuperAdmin(BasePermission):
    """
    Custom permission to allow only super_admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'super_admin'

class IsOwnerOrAdminOrStaff(BasePermission):
    """
    Custom permission to allow only the owner or admins to edit/delete an object.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Write permissions are only allowed to the owner or an admin
        return (
            obj.user == request.user or 
            request.user.role in ('admin', 'staff')
        )
