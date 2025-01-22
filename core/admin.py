from django.contrib import admin
from .models import InventoryItem, Office, ItemRegister

# Register your models here.

class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'created_at')
    search_fields = ('name', 'user__username')  # Allows searching by item name and user
    list_filter = ('created_at', 'department')        # Adds filtering options

admin.site.register(Office, OfficeAdmin)


# Optional: Customize how the model appears in the admin
class ItemRegisterAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'name', 'description', 'created_at')  # Display these fields in the list view
    search_fields = ('item_id', 'name')  # Allow searching by item_id and name
    list_filter = ('created_at',)  # Filter by created_at in the admin interface
    ordering = ('created_at',)  # Order by created_at by default

# Register the model with the custom admin class
admin.site.register(ItemRegister, ItemRegisterAdmin)


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('office', 'item_name', 'quantity', 'remarks', 'year')  # Add item_name method
    
    def item_name(self, obj):
        return obj.item_id.name  # Access 'name' through the ForeignKey 'item_id'
    item_name.admin_order_field = 'item_id__name'  # Allows sorting by 'item_id__name'
    item_name.short_description = 'Item Name'  # Custom column header in admin
    
    search_fields = ('item_id__name', 'office__name')
    list_filter = ('year', 'office')
    
admin.site.register(InventoryItem, InventoryItemAdmin)