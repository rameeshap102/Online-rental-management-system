from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings


# choices
DISTRICT_CHOICES = [
    ('alappuzha', 'Alappuzha'),
    ('ernakulam', 'Ernakulam'),
    ('idukki', 'Idukki'),
    ('kannur', 'Kannur'),
    ('kasaragod', 'Kasaragod'),
    ('kollam', 'Kollam'),
    ('kottayam', 'Kottayam'),
    ('kozhikode', 'Kozhikode'),
    ('malappuram', 'Malappuram'),
    ('palakkad', 'Palakkad'),
    ('pathanamthitta', 'Pathanamthitta'),
    ('thiruvananthapuram', 'Thiruvananthapuram'),
    ('thrissur', 'Thrissur'),
    ('wayanad', 'Wayanad'),
]
PROPERTY_TYPE_CHOICES = [
    ('apartment', 'Apartment'),
    ('studio', 'Studio'),
    ('villa', 'Villa'),
    ('house', 'House'),
]

# ======================
# Custom User Model
# ======================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=[("landlord", "Landlord"), ("tenant", "Tenant")],
        default="tenant"
    )
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# ======================
# Profile Model
# ======================
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.email


# ======================
# Property Model
# ======================
class Property(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'landlord'}
    )
    title = models.CharField(max_length=200)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, default='alappuzha' )
    address = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    size = models.PositiveIntegerField(default=0, help_text="Size in sq ft")
    property_type = models.CharField(
        max_length=50,
        choices=PROPERTY_TYPE_CHOICES
    )
    image = models.ImageField(upload_to="properties/", blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ======================
# Booking Model
# ======================
class Booking(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    application = models.OneToOneField(
        'Application', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='booking'
    )
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user} - {self.property} ({self.status})"


# ======================
# Payment Model
# ======================
class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)  # optional if you want a due date
    month = models.DateField(null=True, blank=True)     # optional month field

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("received", "Received"),
        ("failed", "Failed"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.booking} - {self.amount} ({self.status})"



# ======================
# Application Model
# ======================
class Application(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="applications")
    message = models.TextField(blank=True, null=True, help_text="Tenant can add a note for the landlord")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    applied_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.email} → {self.property.title} ({self.status})"

# ======================
# Maintenance Model
# ======================

class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    CATEGORY_CHOICES = [
        ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing'),
        ('other', 'Other'),
    ]

    property = models.ForeignKey("Property", on_delete=models.CASCADE)
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    issue = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # optional

    def __str__(self):
        return f"{self.property.title} - {self.tenant.email} - {self.status}"



class MaintenanceRequest(models.Model):
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="maintenance_requests")
    property = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="maintenance_requests")
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)