from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrStaffOrReadOnly(BasePermission):
    """
    Allows read-only access for all users, but restricts edit/delete to admins, staff, and superusers.
    Superusers and superadmins have unrestricted access.
    """
    def has_permission(self, request, view):
        # Allow read-only methods for everyone
        if request.method in SAFE_METHODS:
            return True

        # Grant access to superusers or superadmins
        if request.user.is_superuser or request.user.role == 'super_admin':
            return True

        # Restrict other methods to authenticated admins and staff
        return request.user.is_authenticated and request.user.role in ('admin', 'staff')

class IsSuperAdminOrSuperUser(BasePermission):
    """
    Grants access only to superadmins (custom role) or Django superusers.
    """
    def has_permission(self, request, view):
        return request.user.is_superuser or (request.user.is_authenticated and request.user.role == 'super_admin')

class IsOwnerOrAdminOrStaff(BasePermission):
    """
    Allows access to the owner, admins, staff, superadmins, or superusers.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read-only access for everyone
        if request.method in SAFE_METHODS:
            return True

        # Grant access to superusers or superadmins
        if request.user.is_superuser or request.user.role == 'super_admin':
            return True

        # Allow edit/delete only for the owner, admins, or staff
        return obj.user == request.user or request.user.role in ('admin', 'staff')

class IsAdminOrSuperAdmin(BasePermission):
    """
    Allows access to admins, superadmins, or superusers.
    """
    def has_permission(self, request, view):
        # Grant access to superusers or superadmins
        if request.user.is_superuser or request.user.role == 'super_admin':
            return True

        # Allow only authenticated admins
        return request.user.is_authenticated and request.user.role == 'admin'

class IsAssignedStaff(BasePermission):
    """
    Ensures staff can only manage inventory for assigned offices.
    Superusers and superadmins have unrestricted access.
    """
    def has_object_permission(self, request, view, obj):
        # Allow access to superusers or superadmins
        if request.user.is_superuser or request.user.role == 'super_admin':
            return True

        # Ensure the user has 'assigned_offices' attribute (valid for staff)
        if hasattr(request.user, 'assigned_offices'):
            # Restrict access to staff assigned to the office in the inventory object
            if obj.office in request.user.assigned_offices.all():
                return True
        
        # Default to denial if none of the conditions are met
        return False

class IsAssignedStaffOrReadOnly(BasePermission):
    """
    Grants read-only access to staff for their assigned offices, and grants full access to admins, superadmins, and superusers.
    """
    def has_permission(self, request, view):
        # Allow read-only methods for everyone
        if request.method in SAFE_METHODS:
            return True

        # Allow full access to superadmins, superusers, or admins
        if request.user.is_superuser or request.user.role in ('super_admin', 'admin'):
            return True

        # Restrict other methods (POST, PUT, DELETE) to authenticated staff for their assigned offices
        return request.user.is_authenticated and request.user.role == 'staff'

    def has_object_permission(self, request, view, obj):
        """
        Ensure staff can only edit/manage inventory for offices they are assigned to.
        """
        # Allow read-only access for everyone
        if request.method in SAFE_METHODS:
            return True

        # Grant full access to superadmins, superusers, or admins
        if request.user.is_superuser or request.user.role in ('super_admin', 'admin'):
            return True

        # Ensure staff can only manage inventory for assigned offices
        if request.user.role == 'staff' and hasattr(request.user, 'assigned_offices'):
            return obj.office in request.user.assigned_offices.all()

        return False
