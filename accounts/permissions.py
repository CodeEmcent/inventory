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

        # Restrict access to staff assigned to the office
        if hasattr(request.user, 'assigned_offices'):
            return obj.office in request.user.assigned_offices.all()

        return False





# from rest_framework.permissions import BasePermission


# class IsAdminOrStaffOrReadOnly(BasePermission):
#     """
#     Custom permission to allow only admins and staff to edit or delete,
#     but everyone can read.
#     """
#     def has_permission(self, request, view):
#         # Allow all users to perform GET, HEAD, or OPTIONS requests (read-only).
#         if request.method in ('GET', 'HEAD', 'OPTIONS'):
#             return True

#         # Allow only authenticated users with 'admin' or 'staff' role to perform other requests.
#         return request.user.is_authenticated and request.user.role in ('admin', 'staff', 'superuser')


# class IsSuperAdmin(BasePermission):
#     """
#     Custom permission to allow only super_admin users.
#     """
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'super_admin'


# class IsOwnerOrAdminOrStaff(BasePermission):
#     """
#     Custom permission to allow only the owner, admins, or staff to edit/delete an object.
#     """
#     def has_object_permission(self, request, view, obj):
#         # Read permissions are allowed for any request
#         if request.method in ('GET', 'HEAD', 'OPTIONS'):
#             return (
#                 request.user.role in ('admin', 'staff') or obj.user == request.user
#             )

#         # Write permissions are only allowed to the owner, admins, or staff
#         return (
#             obj.user == request.user or
#             request.user.role in ('admin', 'staff')
#         )

# class IsAdminOrSuperAdmin(BasePermission):
#     """
#     Custom permission to allow only admin, super_admin users, or superusers.
#     """
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and (
#             request.user.is_superuser or
#             request.user.role in ('admin', 'super_admin')
#         )

# class IsAssignedStaff(BasePermission):
#     """
#     Custom permission to ensure staff can only manage inventory for assigned offices.
#     """
#     def has_object_permission(self, request, view, obj):
#         # Allow access if the user is an admin or superadmin
#         if request.user.role in ('admin', 'super_admin'):
#             return True

#         # Check if the user is assigned to the office
#         # Add a safeguard to ensure `assigned_offices` exists
#         if hasattr(request.user, 'assigned_offices'):
#             return obj.office in request.user.assigned_offices.all()

#         return False
