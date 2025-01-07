from django.contrib import admin
from .models import InventoryItem

# Register your models here.

class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'quantity', 'user', 'created_at')
    search_fields = ('name', 'user__username')  # Allows searching by item name and user
    list_filter = ('created_at', 'user')        # Adds filtering options

admin.site.register(InventoryItem, InventoryItemAdmin)