from rest_framework import serializers
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
        fields = ['username', 'password', 'organization']
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

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'profile', 'organization', 'assigned_offices']
        depth = 1  # Expands related fields like organization and assigned_offices for detailed view


class OfficeAssignmentSerializer(serializers.ModelSerializer):
    assigned_offices = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Office.objects.all()
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'assigned_offices']

    def validate(self, data):
        """
        Ensure offices are uniquely assigned to staff users.
        """
        user = self.instance
        if user.role != 'staff':
            return data  # No restriction for non-staff users

        # Check for duplicate office assignments
        for office in data.get('assigned_offices', []):
            if office.assigned_users.exclude(id=user.id).exists():
                raise serializers.ValidationError(
                    f"Office '{office.name}' is already assigned to another staff user."
                )

        return data
