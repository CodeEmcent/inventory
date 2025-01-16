from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Organization, Profile
from django.contrib.auth.models import Group

class ProfileInline(admin.StackedInline):  # Use TabularInline for a table-like format
    model = Profile
    can_delete = False  # Set this to True if you want to allow profile deletion directly from user admin
    verbose_name_plural = 'Profile'  # This is the title of the profile section in the admin

class CustomUserAdmin(UserAdmin):
    # List the fields to display in the user list page of the admin
    list_display = ('username', 'email', 'role', 'organization', 'get_assigned_offices')

    # Add the `organization` field to the user edit form in the admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('organization', 'assigned_offices')}),  # Include custom fields like organization
    )
    
    # Define a method to display the list of assigned offices
    def get_assigned_offices(self, obj):
        return ", ".join([office.name for office in obj.assigned_offices.all()])
    
    get_assigned_offices.short_description = 'Assigned Offices'  # This will show up as the column header

    # Make sure you have the proper filtering options
    search_fields = ('username', 'email', 'role', 'organization__name')  # Search by organization name as well
    filter_horizontal = ('assigned_offices',)  # Allows better UI for selecting offices in the admin

    # Register ProfileInline in the admin
    inlines = [ProfileInline]  # Add Profile inline model here

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            raise ValueError("Only super admins can assign admin or super admin roles.")
        super().save_model(request, obj, form, change)

# Registering the CustomUser model with the custom UserAdmin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Organization)