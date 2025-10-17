from django.core.management.base import BaseCommand
from rentalapp.models import CustomUser

class Command(BaseCommand):
    help = 'Creates a superuser if it does not exist'

    def handle(self, *args, **options):
        email = 'admin@rental.com'
        password = 'admin@123'
        
        if not CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.create(
                email=email,
                first_name='Admin',
                last_name='User',
                role='landlord',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser created: {email}'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Superuser already exists'))
