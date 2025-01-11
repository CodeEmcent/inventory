from rest_framework import serializers
from .models import Office, InventoryItem

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'user', 'office', 'name', 'quantity', 'description',
            'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'office']



class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name', 'department', 'user', 'created_at']
        read_only_fields = ['created_at']