from django.core.management.base import BaseCommand
from accounts.models import CustomUser, Organization


class Command(BaseCommand):
    help = "Create an admin user for an organization"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help="The admin's username")
        parser.add_argument('--email', type=str, required=True, help="The admin's email")
        parser.add_argument('--password', type=str, required=True, help="The admin's password")
        parser.add_argument('--organization', type=str, required=True, help="The organization name")

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        password = kwargs['password']
        org_name = kwargs['organization']

        # Create or retrieve the organization
        organization, created = Organization.objects.get_or_create(name=org_name)

        # Create the admin user
        admin_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin',
            organization=organization
        )

        self.stdout.write(
            self.style.SUCCESS(f"Admin user '{admin_user.username}' created successfully for organization '{organization.name}'.")
        )
