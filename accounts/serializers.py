from rest_framework import serializers
from .models import CustomUser, Organization
from rest_framework import serializers
from accounts.models import CustomUser
from core.models import Office

class RegisterUserSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'role', 'organization']
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
            role=validated_data.get('role', 'staff'),
            organization=organization,
        )
        return user

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'organization', 'assigned_offices']
        depth = 1  # Expand relationships (e.g., organization, offices)


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
