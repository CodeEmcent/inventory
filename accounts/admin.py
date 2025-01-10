from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Organization

# Register your models here.

class CustomUserAdmin(UserAdmin):
    # List the fields to display in the user list page of the admin
    list_display = ('username', 'email', 'organization', 'get_assigned_offices')

    # Add the `assigned_offices` to the user edit form in the admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('assigned_offices',)}),  # Adding the many-to-many field
    )
    
    # Define a method to display the list of assigned offices
    def get_assigned_offices(self, obj):
        return ", ".join([office.name for office in obj.assigned_offices.all()])
    
    get_assigned_offices.short_description = 'Assigned Offices'  # This will show up as the column header

    # Make sure you have the proper filtering options
    search_fields = ('username', 'email', 'role')
    filter_horizontal = ('assigned_offices',)  # Allows better UI for selecting offices in the admin

# Registering the CustomUser model with the custom UserAdmin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Organization)