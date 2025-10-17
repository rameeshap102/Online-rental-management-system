from django.contrib import admin
from .models import Profile, Property, Booking, Payment

admin.site.register(Profile)
admin.site.register(Property)
admin.site.register(Booking)
admin.site.register(Payment)
