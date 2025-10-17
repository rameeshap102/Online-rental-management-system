from django.core.management.base import BaseCommand
from rentalapp.models import CustomUser
import os

class Command(BaseCommand):
    help = 'Creates a superuser if it does not exist'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@rental.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin@123')
        
        if not CustomUser.objects.filter(username=username).exists():
            CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                user_type='landlord'
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser created: {username}'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Superuser already exists'))
