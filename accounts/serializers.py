from rest_framework import serializers
from .models import CustomUser, Organization

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
            role=validated_data.get('role', 'viewer'),
            organization=organization,
        )
        return user
