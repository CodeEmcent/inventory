from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .serializers import (
    RegisterUserSerializer, 
    OfficeAssignmentSerializer,
    UserListSerializer,
    ProfileSerializer, 
)
from accounts.permissions import IsAdminOrSuperAdmin
from accounts.models import CustomUser, Profile


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Accepting profile data as well in the serializer
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user
            user = serializer.save()

            # Create profile for the user directly in the serializer (optional)
            profile_data = {
                'user': user,
                'organization': request.data.get('organization', ''),
                'bio': request.data.get('bio', ''),
                'profile_picture': request.data.get('profile_picture', None)
            }
            # Ensure that profile creation is tied to user registration
            profile, created = Profile.objects.get_or_create(user=user, defaults=profile_data)

            return Response({"message": "User registered successfully."}, status=201)
        return Response(serializer.errors, status=400)


class UserProfileView(APIView):
    """
    Get or update the current user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile  # Since we have a one-to-one relationship
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the profile data
        serializer = ProfileSerializer(profile)
        return Response({"message": "User profile fetched successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        try:
            profile = user.profile  # Fetch user's profile
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Deserialize the profile data to update
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class AllUsersView(APIView):
    """
    Endpoint to list all users (staff, admin, super admin).
    Restricted to admins and super admins.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request):
        # Admins and Superadmins can see all users (staff, admin, super_admin)
        if request.user.role in ['admin', 'super_admin']:
            users = CustomUser.objects.all()  # Fetch all users
        else:
            users = CustomUser.objects.filter(role='staff')  # Only fetch staff users for non-admins

        serializer = UserListSerializer(users, many=True)
        return Response({
            "message": "All staff users retrieved successfully.",
            "data": serializer.data
        }, status=200)


class AssignOfficesView(APIView):
    """
    Allows admins or superadmins to assign offices to staff.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, user_id):
        try:
            # Fetch the user
            user = CustomUser.objects.get(id=user_id)

            # Ensure the user is a staff member
            if user.role != 'staff':
                return Response({"error": "Only staff users can be assigned offices."}, status=400)

            # Serialize and validate data
            serializer = OfficeAssignmentSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": f"Offices assigned successfully to {user.username}.",
                    "data": serializer.data
                }, status=200)

            return Response(serializer.errors, status=400)

        except CustomUser.DoesNotExist:
            return Response({"error": "Staff user not found."}, status=404)

    def get(self, request):
        offices = request.user.assigned_offices.all().values('id', 'name', 'department')
        return Response({"offices": list(offices)})



# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework import status
# from .serializers import (
#     RegisterUserSerializer, 
#     OfficeAssignmentSerializer,
#     UserListSerializer,
#     ProfileSerializer, 
# )
# from accounts.permissions import IsAdminOrSuperAdmin
# from accounts.models import CustomUser, Profile


# class RegisterUserView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         # Ensure you're also accepting profile data
#         serializer = RegisterUserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()

#             # Create a profile for the user
#             profile_data = {
#                 'organization': request.data.get('organization', ''),
#                 'bio': request.data.get('bio', ''),
#                 'profile_picture': request.data.get('profile_picture', None)
#             }
#             Profile.objects.create(user=user, **profile_data)

#             return Response({"message": "User registered successfully."}, status=201)
#         return Response(serializer.errors, status=400)


# class UserProfileView(APIView):
#     """
#     Get or update the current user's profile.
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         # Fetch the profile
#         try:
#             profile = user.profile  # Since we have a one-to-one relationship
#         except Profile.DoesNotExist:
#             return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

#         # Serialize the profile data
#         serializer = ProfileSerializer(profile)
#         return Response({"message": "User profile fetched successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

#     def put(self, request):
#         user = request.user
#         try:
#             profile = user.profile  # Fetch user's profile
#         except Profile.DoesNotExist:
#             return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

#         # Deserialize the profile data to update
#         serializer = ProfileSerializer(profile, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Profile updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
#         return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# class LogoutView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             refresh_token = request.data["refresh"]
#             token = RefreshToken(refresh_token)
#             token.blacklist()
#             return Response({"message": "Logout successful."}, status=200)
#         except Exception as e:
#             return Response({"error": str(e)}, status=400)


# class AllUsersView(APIView):
#     """
#     Endpoint to list all users (staff, admin, super admin).
#     Restricted to admins and super admins.
#     """
#     permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

#     def get(self, request):
#         # Admins and Superadmins can see all users (staff, admin, super_admin)
#         if request.user.role in ['admin', 'super_admin']:
#             users = CustomUser.objects.all()  # Fetch all users
#         else:
#             users = CustomUser.objects.filter(role='staff')  # Only fetch staff users for non-admins

#         serializer = UserListSerializer(users, many=True)
#         return Response({
#             "message": "All staff users retrieved successfully.",
#             "data": serializer.data
#         }, status=200)


# class AssignOfficesView(APIView):
#     """
#     Allows admins or superadmins to assign offices to staff.
#     """
#     permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

#     def post(self, request, user_id):
#         try:
#             # Fetch the user
#             user = CustomUser.objects.get(id=user_id)

#             # Ensure the user is a staff member
#             if user.role != 'staff':
#                 return Response({"error": "Only staff users can be assigned offices."}, status=400)

#             # Serialize and validate data
#             serializer = OfficeAssignmentSerializer(user, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response({
#                     "message": f"Offices assigned successfully to {user.username}.",
#                     "data": serializer.data
#                 }, status=200)

#             return Response(serializer.errors, status=400)

#         except CustomUser.DoesNotExist:
#             return Response({"error": "Staff user not found."}, status=404)

#     def get(self, request):
#         offices = request.user.assigned_offices.all().values('id', 'name', 'department')
#         return Response({"offices": list(offices)})
