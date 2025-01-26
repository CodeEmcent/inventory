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
        token["role"] = user.role  # Add custom claims
        return token

    def validate(self, attrs):
        username_or_email = attrs.get("username")  # Expect frontend to send this as "username"
        password = attrs.get("password")

        if not username_or_email or not password:
            raise AuthenticationFailed("Username/email and password are required")

        try:
            # Find user by email or username (case-insensitive)
            user = User.objects.get(email__iexact=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=username_or_email)
            except User.DoesNotExist:
                raise AuthenticationFailed("Invalid username/email")

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password")

        # Validate and return token
        attrs["username"] = user.username  # Required for parent class validation
        data = super().validate(attrs)
        data["role"] = user.role
        return data

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

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name', 'description']

class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()  # Combine first_name and last_name
    username = serializers.CharField(source='user.username')  # Include username explicitly
    role = serializers.CharField(source='user.role')  # User role
    organization = serializers.CharField(source='user.organization.name', default="No organization")
    assigned_offices = serializers.SerializerMethodField()  # Assigned offices
    profile_picture = serializers.ImageField()  # Use ImageField for full URL

    class Meta:
        model = Profile
        fields = ['username', 'name', 'role', 'organization', 'assigned_offices', 'profile_picture', 'bio']

    def get_name(self, obj):
        """
        Combine the first_name and last_name fields of the related user.
        If both are empty, default to the username.
        """
        first_name = obj.user.first_name or ""
        last_name = obj.user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()  # Remove extra spaces
        return full_name if full_name else obj.user.username
    
    def get_profile_picture(self, obj):
        request = self.context.get('request')  # Get the request from serializer context
        if obj.profile_picture:
            return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_assigned_offices(self, obj):
        # Return the office names the user is assigned to
        return [office.name for office in obj.user.assigned_offices.all()]

    def update(self, instance, validated_data):
        # Update profile fields and linked user fields
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.bio = validated_data.get('bio', instance.bio)

        # Update related user data
        user_data = validated_data.get('user', {})
        if 'organization' in user_data:
            instance.user.organization = user_data['organization']
            instance.user.save()

        instance.save()  # Save the profile instance
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
