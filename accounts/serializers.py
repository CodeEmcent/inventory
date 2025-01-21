from rest_framework import serializers
from django.db.models import Count, Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from accounts.models import CustomUser, Profile, Organization
from core.models import Office

User = get_user_model()

# In your backend account serializer, modify CustomTokenObtainPairSerializer
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role  # Assuming the User model has a `role` field
        return token

    def validate(self, attrs):
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        try:
            # Attempt to find user by email
            user = User.objects.get(email=username_or_email)
        except User.DoesNotExist:
            try:
                # Fallback to username
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                raise AuthenticationFailed("Invalid credentials")

        # Set the username for further validation
        attrs["username"] = user.username

        # Call the base validate method
        validated_data = super().validate(attrs)

        # Add the role to the validated data (this will be included in the JWT response)
        validated_data['role'] = user.role

        return validated_data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterUserSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'organization']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Handle organization
        organization_name = validated_data.pop('organization', None)
        organization = None
        if organization_name:
            organization, _ = Organization.objects.get_or_create(name=organization_name)

        # Create the user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            password=validated_data['password'],
            organization=organization,
        )
        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['organization', 'profile_picture', 'bio']

    def update(self, instance, validated_data):
        # Update profile fields
        instance.organization = validated_data.get('organization', instance.organization)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.save()
        return instance

class UserListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()  # Nested ProfileSerializer to include profile information
    organization = serializers.StringRelatedField()  # Displaying the name of the organization
    assigned_offices = serializers.SerializerMethodField()

    def get_assigned_offices(self, obj):
        return [{"id": office.id, "name": office.name} for office in obj.assigned_offices.all()]

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'profile', 'organization', 'assigned_offices']
        depth = 1  # Expands related fields like organization and assigned_offices for detailed view

class OfficeAssignmentSerializer(serializers.ModelSerializer):
    assigned_offices = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Office.objects.all()
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'assigned_offices']

    def validate_assigned_offices(self, assigned_offices):
        """
        Ensure offices are uniquely assigned to staff users.
        """
        user = self.instance

        # No restrictions for non-staff users
        if user.role != 'staff':
            return assigned_offices

        # Get IDs of offices already assigned to other staff users
        conflicting_offices = (
            Office.objects.filter(id__in=[office.id for office in assigned_offices])
            .exclude(assigned_users=user)
            .annotate(other_staff_count=Count('assigned_users', filter=Q(assigned_users__role='staff')))
            .filter(other_staff_count__gt=0)
        )

        if conflicting_offices.exists():
            conflict_details = ", ".join(
                f"{office.name} (assigned to: {', '.join([u.username for u in office.assigned_users.filter(role='staff')])})"
                for office in conflicting_offices
            )
            raise serializers.ValidationError(
                f"The following offices are already assigned to other staff users: {conflict_details}"
            )

        return assigned_offices

    def validate(self, data):
        """
        Perform additional cross-field validations if needed.
        """
        # Validate assigned_offices specifically
        data['assigned_offices'] = self.validate_assigned_offices(data.get('assigned_offices', []))
        return data
