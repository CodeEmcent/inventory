from rest_framework.permissions import BasePermission


class IsAdminOrStaffOrReadOnly(BasePermission):
    """
    Custom permission to allow only admins and staff to edit or delete,
    but everyone can read.
    """
    def has_permission(self, request, view):
        # Allow all users to perform GET, HEAD, or OPTIONS requests (read-only).
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Allow only authenticated users with 'admin' or 'staff' role to perform other requests.
        return request.user.is_authenticated and request.user.role in ('admin', 'staff')


class IsSuperAdmin(BasePermission):
    """
    Custom permission to allow only super_admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'super_admin'


class IsOwnerOrAdminOrStaff(BasePermission):
    """
    Custom permission to allow only the owner, admins, or staff to edit/delete an object.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Write permissions are only allowed to the owner, admins, or staff
        return (
            obj.user == request.user or
            request.user.role in ('admin', 'staff')
        )


class IsAdminOrSuperAdmin(BasePermission):
    """
    Custom permission to allow only admin or super_admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('admin', 'super_admin')


class IsAssignedStaff(BasePermission):
    """
    Custom permission to ensure staff can only manage inventory for assigned offices.
    """
    def has_object_permission(self, request, view, obj):
        # Allow access if the user is an admin or superadmin
        if request.user.role in ('admin', 'super_admin'):
            return True

        # Check if the user is assigned to the office
        # Add a safeguard to ensure `assigned_offices` exists
        if hasattr(request.user, 'assigned_offices'):
            return obj.office in request.user.assigned_offices.all()

        return False
