from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import EmailAuthenticationForm

urlpatterns = [
    # Public pages
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("browse/", views.property_list, name="browse_properties"),
    path("get-started/", views.get_started, name="get_started"),
    path("list-property/", views.list_property_redirect, name="list_property_redirect"),

    # Properties
    path("properties/", views.property_list, name="property_list"),
    path("properties/add/", views.add_property, name="add_property"),
    path("properties/<int:pk>/", views.property_detail, name="property_detail"),
    path("properties/<int:property_id>/book/", views.book_property, name="book_property"),
    path("properties/<int:property_id>/contact/", views.contact_landlord, name="contact_landlord"),

    # Auth
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(
        template_name="rentalapp/login.html",
        authentication_form=EmailAuthenticationForm,
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

    # Dashboards
    path("landlord/dashboard/", views.landlord_dashboard, name="landlord_dashboard"),
    path("tenant/dashboard/", views.tenant_dashboard, name="tenant_dashboard"),
    path("tenant/", views.tenant_dashboard_overview, name="tenant_dashboard_overview"),

    # Tenant
    path("tenant/bookings/", views.tenant_bookings, name="tenant_bookings"),
    path("tenant/bookings/<str:status>/", views.tenant_bookings, name="tenant_bookings_filtered"),
    path("tenant/applications/", views.tenant_applications, name="tenant_applications"),
    path("tenant/payments/", views.tenant_payments, name="tenant_payments"),
    path("tenant/maintenance/", views.tenant_maintenance, name="tenant_maintenance"),
    path("tenant/profile/", views.tenant_profile, name="tenant_profile"),
    path("tenant/profile/edit/", views.edit_profile, name="edit_profile"),
    path("tenant/application/<int:app_id>/cancel/", views.cancel_application, name="cancel_application"),

    # Landlord
    path("landlord/profile/", views.profile_view, name="landlord_profile"),
    path("landlord/profile/edit/", views.edit_profile, name="landlord_edit_profile"),
    path("landlord/bookings/", views.landlord_bookings, name="bookings"),
    path("landlord/applications/", views.landlord_applications, name="applications"),
    path("landlord/payments/", views.landlord_payments, name="payments"),
    path("landlord/maintenance/", views.landlord_maintenance, name="maintenance"),
    path("landlord/maintenance/update/<int:pk>/", views.update_maintenance, name="update_maintenance"),
    # Landlord – My Properties (only owned by landlord)
    path("landlord/my-properties/", views.landlord_properties, name="landlord_properties"),
    path('landlord/add-property/', views.add_property, name='add_property'),
    path('landlord/edit-property/<int:pk>/', views.edit_property, name='edit_property'),
    path('landlord/delete-property/<int:pk>/', views.delete_property, name='delete_property'),

    # Actions
    path("booking/cancel/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("payment/<int:booking_id>/", views.make_payment, name="make_payment"),

    # Static pages
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("help/", views.help_center, name="help"),
]
