from django.core.management.base import BaseCommand
from django.urls import get_resolver

class Command(BaseCommand):
    help = 'Shows all registered URLs'

    def handle(self, *args, **options):
        print("\n--- Registered URLs ---")
        for pattern in get_resolver().url_patterns:
            print(pattern)
        print("--- End of Registered URLs ---\n")
