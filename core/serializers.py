from rest_framework import serializers
from .models import Office, ItemRegister, InventoryItem

class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name', 'department', 'created_at']
        read_only_fields = ['created_at']

class ItemRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemRegister
        fields = ['id', 'item_id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class InventoryItemSerializer(serializers.ModelSerializer):
    # Use SlugRelatedField to link 'item_id' (the string) to the ItemRegister object
    item_id = serializers.SlugRelatedField(queryset=ItemRegister.objects.all(), slug_field='item_id')
    item_name = serializers.CharField(source='item_id.name', read_only=True)
    office_name = serializers.CharField(source='office.name', read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'user', 'office', 'office_name', 'item_id', 'item_name', 'quantity',
            'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'office']
