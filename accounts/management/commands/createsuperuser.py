from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management import CommandError
from accounts import CustomUser

class Command(BaseCommand):
    def handle(self, *args, **options):
        options['role'] = 'super_admin'  # Explicitly set the role
        super().handle(*args, **options)

        username = options.get('username')
        user = CustomUser.objects.get(username=username)
        if user.role != 'super_admin':
            raise CommandError("Superuser role was not set correctly.")
