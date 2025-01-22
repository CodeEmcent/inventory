from rest_framework.views import APIView
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .serializers import (
    RegisterUserSerializer,
    OfficeAssignmentSerializer,
    UserListSerializer,
    ProfileSerializer,
    CustomTokenObtainPairSerializer,  # Import the custom JWT serializer
)
from accounts.permissions import IsAdminOrSuperAdmin
from accounts.models import CustomUser, Profile, Organization
from core.models import Office
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Accepting profile data as well in the serializer
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user
            user = serializer.save()

            # Handle organization association
            organization_name = request.data.get("organization", "").strip()
            organization = None
            if organization_name:
                organization, _ = Organization.objects.get_or_create(
                    name=organization_name
                )

            # Create or update the profile
            profile_data = {
                "organization": organization,
                "bio": request.data.get("bio", "").strip(),
                "profile_picture": request.data.get("profile_picture", None),
            }
            Profile.objects.update_or_create(user=user, defaults=profile_data)

            return Response({"message": "User registered successfully."}, status=201)

        # Handle validation errors
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
            return Response(
                {"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the profile data
        serializer = ProfileSerializer(profile)
        return Response(
            {"message": "User profile fetched successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        user = request.user
        try:
            profile = user.profile  # Fetch user's profile
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Deserialize the profile data to update
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.all()  # Fetch all users
        organizations = Organization.objects.all()  # Fetch all organizations
        offices = Office.objects.all()  # Fetch all offices

        # Serialize users
        users_data = UserListSerializer(users, many=True).data

        # Include organizations and offices in the response
        return Response(
            {
                "users": users_data,
                "organizations": [
                    {"id": org.id, "name": org.name} for org in organizations
                ],
                "offices": [
                    {"id": office.id, "name": office.name} for office in offices
                ],
            }
        )

class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def put(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = UserListSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "User updated successfully.", "data": serializer.data},
                    status=200,
                )
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def delete(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            user.delete()
            return Response({"message": "User deleted successfully."}, status=200)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

class StaffAndOfficesView(APIView):
    """
    Allows fetching of all staff users and the offices assigned to them.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Fetch all staff users
            staff_users = CustomUser.objects.filter(role='staff')
            
            # Prepare the data
            staff_data = []
            for staff in staff_users:
                # Serialize the staff user data including assigned offices
                serializer = OfficeAssignmentSerializer(staff)
                staff_data.append({
                    'staff_user': serializer.data,
                    'assigned_offices': [
                        {
                            'id': office.id,
                            'name': office.name,
                            'department': office.department
                        } 
                        for office in staff.assigned_offices.all()
                    ]
                })

            return Response({"staff_and_offices": staff_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            # Fetch the specific user by ID
            user = CustomUser.objects.get(id=user_id)
            # Serialize the user data
            user_data = UserListSerializer(user).data
            return Response({"user": user_data})
        except CustomUser.DoesNotExist:
            raise NotFound({"error": "User not found"})

class AssignOfficesView(APIView):
    """
    Allows admins or superadmins to assign, update, delete, or append offices for staff users.
    """

    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, user_id):
        """
        Assign new offices to a staff user.
        Appends to existing assignments without overwriting them.
        """
        try:
            user = CustomUser.objects.get(id=user_id)

            # Ensure the user is a staff member
            if user.role != "staff":
                return Response({"error": "Only staff users can be assigned offices."}, status=400)

            # Retrieve current assignments and merge with new ones
            current_offices = set(user.assigned_offices.values_list("id", flat=True))
            new_offices = set(request.data.get("assigned_offices", []))
            all_offices = current_offices | new_offices  # Union of old and new assignments

            # Update assignments
            user.assigned_offices.set(all_offices)
            user.save()

            return Response(
                {
                    "message": f"Offices assigned successfully to {user.username}.",
                    "assigned_offices": list(all_offices),
                },
                status=status.HTTP_200_OK,
            )
        except CustomUser.DoesNotExist:
            return Response({"error": "Staff user not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, user_id):
        """
        Update the offices assigned to a staff user.
        Replaces all existing assignments with the provided list.
        """
        try:
            user = CustomUser.objects.get(id=user_id)

            # Ensure the user is a staff member
            if user.role != "staff":
                return Response({"error": "Only staff users can be assigned offices."}, status=400)

            # Replace assignments with the provided list
            updated_offices = request.data.get("assigned_offices", [])
            user.assigned_offices.set(updated_offices)
            user.save()

            return Response(
                {
                    "message": f"Offices updated successfully for {user.username}.",
                    "assigned_offices": updated_offices,
                },
                status=status.HTTP_200_OK,
            )
        except CustomUser.DoesNotExist:
            return Response({"error": "Staff user not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id):
        """
        Remove one or more assigned offices from a staff user.
        """
        try:
            user = CustomUser.objects.get(id=user_id)

            # Ensure the user is a staff member
            if user.role != "staff":
                return Response({"error": "Only staff users can have offices removed."}, status=400)

            # Retrieve offices to be removed
            offices_to_remove = set(request.data.get("assigned_offices", []))
            current_offices = set(user.assigned_offices.values_list("id", flat=True))

            # Calculate remaining offices
            remaining_offices = current_offices - offices_to_remove
            user.assigned_offices.set(remaining_offices)
            user.save()

            return Response(
                {
                    "message": f"Offices removed successfully for {user.username}.",
                    "remaining_offices": list(remaining_offices),
                },
                status=status.HTTP_200_OK,
            )
        except CustomUser.DoesNotExist:
            return Response({"error": "Staff user not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, user_id=None):
        """
        Retrieve assigned offices for a specific user or all staff users.
        """
        try:
            if user_id:
                user = CustomUser.objects.get(id=user_id)
                assigned_offices = [
                    {"id": office.id, "name": office.name, "department": office.department}
                    for office in user.assigned_offices.all()
                ]
                return Response({"assigned_offices": assigned_offices}, status=status.HTTP_200_OK)
            else:
                # Fetch all staff users with their assigned offices
                staff_users = CustomUser.objects.filter(role="staff").select_related("assigned_offices")
                staff_offices = [
                    {
                        "user_id": user.id,
                        "username": user.username,
                        "assigned_offices": [
                            {"id": office.id, "name": office.name, "department": office.department}
                            for office in user.assigned_offices.all()
                        ],
                    }
                    for user in staff_users
                ]
                return Response({"staff_and_offices": staff_offices}, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({"error": "Staff user not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RemoveOfficesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request):
        office_id = request.data.get("office_id")
        user_id = request.data.get("user_id")

        try:
            user = CustomUser.objects.get(id=user_id)
            office = Office.objects.get(id=office_id)

            # Remove the office from the user's assignments
            user.assigned_offices.remove(office)
            user.save()

            return Response(
                {"message": "Office assignment removed successfully."},
                status=status.HTTP_200_OK,
            )

        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Office.DoesNotExist:
            return Response({"error": "Office not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
