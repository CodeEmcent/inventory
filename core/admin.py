from django.contrib import admin
from .models import InventoryItem, Office

# Register your models here.

class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'created_at')
    search_fields = ('name', 'user__username')  # Allows searching by item name and user
    list_filter = ('created_at', 'department')        # Adds filtering options

admin.site.register(Office, OfficeAdmin)


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'office', 'quantity', 'created_at', 'updated_at']
    search_fields = ['name', 'user__username', 'office__name']
    list_filter = ['office', 'user']

admin.site.register(InventoryItem, InventoryItemAdmin)