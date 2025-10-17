from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db import models  # For Sum
from django.urls import reverse
from .forms import CustomUserCreationForm, EmailAuthenticationForm, PropertyForm, BookingForm
from django.core.mail import send_mail
from django.contrib import messages
from django.views import View
from .models import Property, Booking, Payment, Maintenance,Application,MaintenanceRequest
from .forms import EditProfileForm ,MaintenanceForm, ProfileForm
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import DISTRICT_CHOICES, PROPERTY_TYPE_CHOICES
User = get_user_model()

# =========================
# Landlord Dashboard
# =========================
@login_required
def landlord_dashboard(request):
    landlord = request.user
    if landlord.role != "landlord":
        return render(request, "rentalapp/forbidden.html")

    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")
        booking = get_object_or_404(Booking, id=booking_id, property__owner=landlord)

        if action == "approve":
            booking.status = "approved"
            booking.save()
            messages.success(request, f"✅ Booking #{booking.id} approved successfully.")
        elif action == "reject":
            booking.status = "rejected"
            booking.save()
            messages.warning(request, f"⚠ Booking #{booking.id} rejected.")

        return redirect("landlord_dashboard")

    total_properties = Property.objects.filter(owner=landlord).count()
    total_income = Payment.objects.filter(
        booking__property__owner=landlord, status="received"
    ).aggregate(total=models.Sum("amount"))["total"] or 0

    total_units = total_properties
    occupied_units = Booking.objects.filter(property__owner=landlord, status="approved").count()
    occupancy_rate = round((occupied_units / total_units) * 100, 1) if total_units > 0 else 0

    applications = Booking.objects.filter(property__owner=landlord, status="pending").count()
    recent_applications = Booking.objects.filter(property__owner=landlord).order_by("-id")[:5]
    payments = Payment.objects.filter(booking__property__owner=landlord).order_by("-date")[:5]

    context = {
        "landlord": landlord,
        "total_properties": total_properties,
        "monthly_income": total_income,
        "occupancy_rate": f"{occupancy_rate}%",
        "applications": applications,
        "recent_applications": recent_applications,
        "payments": payments,
    }
    return render(request, "rentalapp/landlord_dashboard.html", context)


# =========================
# Tenant Dashboard
# =========================
@login_required
def tenant_dashboard(request):
    tenant = request.user
    if tenant.role != "tenant":
        return render(request, "rentalapp/forbidden.html")

    active_bookings = Booking.objects.filter(user=tenant, status="approved")
    pending_bookings = Booking.objects.filter(user=tenant, status="pending")
    all_payments = Payment.objects.filter(booking__user=tenant, status="received")
    total_spent = all_payments.aggregate(total=models.Sum("amount"))["total"] or 0
    payments = all_payments.order_by("-date")[:5]

    context = {
        "tenant": tenant,
        "active_bookings": active_bookings,
        "pending_bookings": pending_bookings,
        "payments": payments,
        "total_spent": total_spent,
    }
    return render(request, "rentalapp/tenant_dashboard.html", context)


# =========================
# Property Redirects & Add
# =========================
@login_required
def list_property_redirect(request):
    if request.user.role == "landlord":
        return redirect("landlord_dashboard")
    messages.error(request, "❌ Only landlords can list properties.")
    return render(request, "rentalapp/forbidden.html", {"no_fade": True})



@login_required
def add_property(request):
    if request.user.role != "landlord":
        messages.error(request, "❌ Only landlords can add properties.")
        return render(request, "rentalapp/forbidden.html")

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.save()
            messages.success(request, f"✅ Property '{prop.title}' added successfully!")
            return redirect("property_list")
        messages.error(request, "❌ Failed to add property. Check the form.")
    else:
        form = PropertyForm()

    return render(request, "rentalapp/property_form.html", {"form": form})


@login_required
def edit_property(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Property '{prop.title}' updated successfully!")
            return redirect("landlord_dashboard")
    else:
        form = PropertyForm(instance=prop)

    return render(request, "rentalapp/property_form.html", {"form": form})

@login_required
def delete_property(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    
    if request.method == "POST":
        prop.delete()
        messages.success(request, f"✅ Property '{prop.title}' has been deleted.")
        return redirect(f"{reverse('landlord_dashboard')}?section=my_properties")
    
    return redirect('landlord_dashboard')



# =========================
# Role-based Login
# =========================
class RoleBasedLoginView(View):
    template_name = "rentalapp/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": EmailAuthenticationForm()})

    def post(self, request):
        email = request.POST.get("username")
        password = request.POST.get("password")
        role_selected = request.POST.get("role")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check DB role
            if user.role != role_selected:
                messages.error(request, f"❌ You selected '{role_selected}', but your account role is '{user.role}'. Access denied.")
                form = EmailAuthenticationForm(request.POST)
                return render(request, self.template_name, {"form": form})

            login(request, user)
            messages.success(request, f"✅ Welcome, {user.username}!")

            # Redirect by role
            if user.role == "landlord":
                return redirect("landlord_dashboard")
            return redirect("tenant_dashboard")
        else:
            messages.error(request, "❌ Invalid credentials. Please try again.")
            form = EmailAuthenticationForm(request.POST)
            return render(request, self.template_name, {"form": form})


# =========================
# Logout
# =========================
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "✅ You have successfully logged out.")
    return redirect("home")


# =========================
# Homepage
# =========================



def home(request):
    DISTRICTS = [
        ('trivandrum', 'Thiruvananthapuram'),
        ('kochi', 'Kochi'),
        ('kollam', 'Kollam'),
        ('alappuzha', 'Alappuzha'),
        ('ernakulam', 'Ernakulam'),
        ('kottayam', 'Kottayam'),
        ('thrissur', 'Thrissur'),
        ('palakkad', 'Palakkad'),
        ('malappuram', 'Malappuram'),
        ('kozhikode', 'Kozhikode'),
        ('wayanad', 'Wayanad'),
        ('kannur', 'Kannur'),
        ('kasaragod', 'Kasaragod'),
    ]

    PROPERTY_TYPES = ["Apartment", "Studio", "Villa", "House"]

   
# Fetch featured properties (limit 3) 
    featured_properties = Property.objects.all()[:3]
 # Start with all properties
    properties = Property.objects.all()
    district = request.GET.get('district')
    max_rent = request.GET.get('max_rent')
    bedrooms = request.GET.get('bedrooms')
    property_type = request.GET.get('property_type')

    if district:
        properties = properties.filter(district=district)
    if max_rent:
        try:
            properties = properties.filter(rent__lte=int(max_rent))
        except ValueError:
            pass
    if bedrooms:
        try:
            properties = properties.filter(bedrooms=int(bedrooms))
        except ValueError:
            pass
    if property_type:
        properties = properties.filter(property_type__iexact=property_type)

    context = {
        "DISTRICTS": DISTRICTS,
        "PROPERTY_TYPES": PROPERTY_TYPE_CHOICES,
          "filtered_properties": properties,
        "featured_properties": featured_properties,
        
    }
    return render(request, "rentalapp/home.html", context)

# =========================
# Signup with role
# =========================
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        role_selected = request.POST.get("role")
        if form.is_valid():
            user = form.save(commit=False)
            if role_selected in ["tenant", "landlord"]:
                user.role = role_selected
            user.save()
            login(request, user)
            messages.success(request, f"✅ Account created successfully! Welcome, {user.username}.")
            if user.role == "landlord":
                return redirect("landlord_dashboard")
            return redirect("tenant_dashboard")
        messages.error(request, "❌ Signup failed. Check the form for errors.")
    else:
        form = CustomUserCreationForm()
    return render(request, "rentalapp/signup.html", {"form": form})


# =========================
# Property Booking
# =========================
@login_required
def book_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    if request.user.role != "tenant":
        messages.error(request, "❌ Only tenants can book properties.")
        return render(request, "rentalapp/forbidden.html", {"no_fade": True})


    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.property = property_obj
            booking.user = request.user
            booking.status = "pending"
            booking.save()
            messages.success(request, f"✅ Booking request for '{property_obj.title}' submitted!")
            return redirect("property_detail", pk=property_id)
        messages.error(request, "❌ Failed to submit booking. Check the form.")
    else:
        form = BookingForm()

    return render(request, "rentalapp/book_property.html", {"property": property_obj, "form": form})


@login_required
def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    return render(request, "rentalapp/property_detail.html", {"property": property_obj})


# =========================
# Contact Landlord
# =========================
@login_required
def contact_landlord(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    if request.user.role != "tenant":
        messages.error(request, "❌ Only tenants are allowed to contact landlords.")
        return render(request, "rentalapp/forbidden.html")

    if request.method == "POST":
        message_text = request.POST.get("message", "").strip()
        if not message_text:
            messages.error(request, "❌ Message cannot be empty.")
            return redirect("property_detail", pk=property_id)

        try:
            send_mail(
                subject=f"Inquiry about {property_obj.title}",
                message=f"From: {request.user.username} ({request.user.email})\n\n{message_text}",
                from_email=request.user.email,
                recipient_list=[property_obj.owner.email],
                fail_silently=False,
            )
            messages.success(request, "✅ Message sent to landlord successfully!")
        except Exception:
            messages.error(request, "❌ Failed to send message. Please try again later.")
        return redirect("property_detail", pk=property_id)

    return render(request, "rentalapp/contact_landlord.html", {"property": property_obj})






# =========================
# Extra Pages
# =========================
def property_list(request):
    properties = Property.objects.all()
    return render(request, "rentalapp/property_list.html", {"properties": properties})

def about(request):
    return render(request, "rentalapp/about.html")


def browse_properties(request):
    return property_list(request)

def get_started(request):
    return render(request, "rentalapp/get_started.html")

def contact(request):
    return render(request, "rentalapp/contact.html")

def terms(request):
    return render(request, "rentalapp/terms.html")

def privacy(request):
    return render(request, "rentalapp/privacy.html")

def help_center(request):
    return render(request, "rentalapp/help.html")


from .forms import MaintenanceForm, ProfileForm
from django.contrib.auth import get_user_model

User = get_user_model()
# -------------------------
# Tenant: Overview 
@login_required
def tenant_dashboard_overview(request):
    # reuse your existing tenant logic but ensure we pass the keys used in template
    tenant = request.user
    # current approved booking (if any)
    active_booking = Booking.objects.filter(user=tenant, status="approved").first()
    # fallback to pending booking if no active booking
    if not active_booking:
        active_booking = Booking.objects.filter(user=tenant, status="pending").first()

    current_property = active_booking.property if active_booking else None
 
      # Stats
    applications_count = Booking.objects.filter(user=tenant, status="pending").count()
    maintenance_requests_count = Maintenance.objects.filter(tenant=tenant).count()
    monthly_rent = current_property.rent if current_property else 0


    context = {
        "section": "overview",
        "tenant": tenant,
        "monthly_rent": monthly_rent,
        "applications_count": applications_count,
        "maintenance_requests": maintenance_requests_count,
        "current_property": current_property,
        "active_booking": active_booking,
    }

    return render(request, "rentalapp/tenant_dashboard.html", context)
# -------------------------
# Tenant: Bookings
# -------------------------
@login_required
def tenant_bookings(request):
    tenant = request.user
    bookings = Booking.objects.filter(user=tenant).order_by("-id")
    return render(request, "rentalapp/tenant_dashboard.html", {
        "section": "bookings",
        "tenant": tenant,
        "bookings": bookings,
    })


# -------------------------
# Tenant Applications
# -------------------------
@login_required
def tenant_applications(request):
    tenant = request.user
    # Only show "pending" bookings here (acts like applications)
    applications = Booking.objects.filter(user=tenant).exclude(status="cancelled").order_by("-id")
    
    return render(request, "rentalapp/tenant_dashboard.html", {
        "section": "applications",
        "tenant": tenant,
        "applications": applications,   
    })


@login_required
def cancel_application(request, app_id):
    application = get_object_or_404(Application, id=app_id, tenant=request.user)

    if application.status == "pending":  
        application.status = "cancelled"
        application.save()
        messages.success(request, "Your application has been cancelled.")
    else:
        messages.error(request, "Only pending applications can be cancelled.")

    return redirect("tenant_dashboard")  # adjust to your dashboard URL name


# -------------------------
# Tenant: Payments
# -------------------------
@login_required
def tenant_payments(request):
    tenant = request.user
    payments = Payment.objects.filter(booking__user=tenant).order_by("-date")
    return render(request, "rentalapp/tenant_dashboard.html", {
        "section": "payments",
        "tenant": tenant,
        "payments": payments,
    })


# -------------------------
# Tenant: Maintenance (list + create)
# -------------------------
@login_required
def tenant_maintenance(request):
    tenant = request.user
    if request.method == "POST":
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            # try to attach to the tenant's active property (if any) or fail fast
            active_booking = Booking.objects.filter(user=tenant, status="approved").first()
            if not active_booking:
                messages.error(request, "You must have an active lease to file maintenance.")
                return redirect("tenant_maintenance")
            m.property = active_booking.property
            m.tenant = tenant
            m.save()
            messages.success(request, "Maintenance request submitted.")
            return redirect("tenant_maintenance")
    else:
        form = MaintenanceForm()

    maintenance_list = Maintenance.objects.filter(tenant=tenant).order_by("-created_at")
    return render(request, "rentalapp/tenant_dashboard.html", {
        "section": "maintenance",
        "tenant": tenant,
        "maintenance_list": maintenance_list,
        "form": form,
    })


# -------------------------
# Tenant: Cancel booking
# -------------------------
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status != "pending":
        messages.error(request, "Only pending bookings can be cancelled.")
        return redirect("tenant_bookings")
    booking.status = "cancelled"
    booking.save()
    messages.success(request, "Booking cancelled.")
    return redirect("tenant_bookings")


# -------------------------
# Tenant: Make payment (simple implementation)
# -------------------------
@login_required
def make_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status="approved")
    if request.method == "POST":
        Payment.objects.create(
            booking=booking,
            amount=booking.property.rent,
            status="received",
            month=date.today().replace(day=1),  # first day of this month
            due_date=date.today() + timedelta(days=7)  # example: 7 days from today
        )
        messages.success(request, "Payment recorded successfully.")
        return redirect("tenant_payments")
    return render(request, "rentalapp/make_payment.html", {"booking": booking})


# -------------------------
# Tenant: Profile view & edit
# -------------------------
@login_required
def tenant_profile(request):
    user = request.user
    form = ProfileForm(instance=user)
    return render(request, "rentalapp/tenant_dashboard.html", {"section": "profile", "tenant": user, "form": form})



@login_required
def landlord_profile(request):
    landlord = request.user  # if your landlord is stored as user
    return render(request, "rentalapp/landlord_dashboard.html", {
        "section": "profile",
        "tenant": landlord,  # for consistency with your template
        "landlord": landlord,
    })


@login_required
def profile_view(request):
    return render(request, "rentalapp/profile.html", {"user": request.user})

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Redirect based on role
            if request.user.role == "tenant":
                return redirect("tenant_profile")
            else:
                return redirect("landlord_profile")
    else:
        form = EditProfileForm(instance=request.user)
    
    return render(request, "rentalapp/edit_profile.html", {"form": form})

def approve_application(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    app.status = "approved"
    app.save()

    # Create booking
    Booking.objects.create(
        user=app.tenant,
        property=app.property,
        application=app,  # link booking to this application
        start_date=date.today(),   # Or your form field
        end_date=date.today() + timedelta(days=365),  # Example: 1 year lease
        status="approved"
    )


@login_required
def landlord_payments(request):
    landlord = request.user
    if landlord.role != "landlord":
        return render(request, "rentalapp/forbidden.html")

    # Fetch payments for this landlord
    payments = Payment.objects.filter(booking__property__owner=landlord).order_by("-date")[:10]  # queryset

    context = {
        "landlord": landlord,
        "payments": payments,
        "section": "payments",  # important for template conditional
    }

    return render(request, "rentalapp/landlord_dashboard.html", context)

@login_required
def landlord_applications(request):
    landlord = request.user
    if landlord.role != "landlord":
        return render(request, "rentalapp/forbidden.html")

    applications = Booking.objects.filter(property__owner=landlord).order_by("-created_at")

    context = {
        "landlord": landlord,
        "applications": applications,
        "section": "applications",
    }
    return render(request, "rentalapp/landlord_dashboard.html", context)



@login_required
def landlord_bookings(request):
    landlord = request.user
    if landlord.role != "landlord":
        return render(request, "rentalapp/forbidden.html")

    bookings = Booking.objects.filter(property__owner=landlord).order_by("-start_date")

    context = {
        "landlord": landlord,
        "bookings": bookings,
        "section": "bookings",
    }
    return render(request, "rentalapp/landlord_dashboard.html", context)

@login_required
def landlord_maintenance(request):
    landlord = request.user
    if landlord.role != "landlord":
        return render(request, "rentalapp/forbidden.html")

    maintenance_requests = Maintenance.objects.filter(
    property__in=properties
).select_related("tenant", "property").order_by("-created_at")


    context = {
        "landlord": landlord,
        "maintenance_requests": maintenance_requests,
        "section": "maintenance",
    }
    return render(request, "rentalapp/landlord_dashboard.html", context)

@login_required
def update_maintenance(request, pk):
    # Only allow the owner of the property to update
    req = get_object_or_404(MaintenanceRequest, pk=pk, property__owner=request.user)

    if request.method == "POST":
        status = request.POST.get("status")
        if status in ["in_progress", "completed"]:
            req.status = status
            req.save()
            messages.success(request, f"Maintenance request #{req.id} updated to {req.status}.")
            return redirect("landlord_maintenance")
@login_required
def landlord_dashboard(request):
    landlord = request.user
    properties = Property.objects.filter(owner=landlord)
    section = request.GET.get('section', 'overview')
    # Handle Approve/Reject actions
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")

        if booking_id and action:
            try:
                booking = Booking.objects.get(id=booking_id, property__in=properties)
                if action == "approve":
                    booking.status = "approved"
                elif action == "reject":
                    booking.status = "rejected"
                booking.save()
            except Booking.DoesNotExist:
                pass

        return redirect(f"{reverse('landlord_dashboard')}?section=applications")

    # Applications (bookings awaiting landlord approval)
    applications_qs = Booking.objects.filter(
        property__in=properties, status="pending"
    ).order_by("-created_at")
    applications_count = applications_qs.count()

    # Recent applications (show 5 latest pending)
    recent_applications = applications_qs[:5]

    # All bookings (approved/active)
    bookings_qs = Booking.objects.filter(property__in=properties).order_by("-start_date")
    bookings_count = bookings_qs.count()

    # Payments (latest 10)
    payments_qs = Payment.objects.filter(
        booking__property__in=properties
    ).order_by("-date")[:10]

    # Maintenance requests (latest 10)
    maintenance_requests = MaintenanceRequest.objects.filter(
        property__in=properties
    ).select_related("tenant", "property").order_by("-created_at")[:10]
    maintenance_count = maintenance_requests.count()

    # Stats
    total_properties = properties.count()
    monthly_income = payments_qs.aggregate(models.Sum("amount"))["amount__sum"] or 0
    occupancy_rate = f"{(bookings_qs.count() / total_properties * 100) if total_properties else 0:.0f}%"

    context = {
        "landlord": landlord,
        "total_properties": total_properties,
        'total_properties': Property.objects.filter(owner=landlord).count(),
        'my_properties': Property.objects.filter(owner=landlord),  
        "monthly_income": monthly_income,
        "occupancy_rate": occupancy_rate,
        "applications": applications_qs,
        "applications_count": applications_count,
        "recent_applications": recent_applications,
        "bookings_count": bookings_count,
        "bookings": bookings_qs,
        "payments": payments_qs,
        "maintenance_requests": maintenance_requests,
        "maintenance_count": maintenance_count,
        "section": request.GET.get("section", "overview"),
    }
    if section == 'my_properties':
        # Fetch only properties owned by this landlord
        context['my_properties'] = Property.objects.filter(owner=landlord)
    return render(request, "rentalapp/landlord_dashboard.html", context)
from django.contrib.auth.decorators import login_required

@login_required
def landlord_properties(request):
    landlord = request.user
    my_properties = Property.objects.filter(owner=landlord)

    context = {
        "section": "my_properties",
        "my_properties": my_properties,
    }
    return render(request, "rentalapp/landlord_dashboard.html", context)



from .models import Property, DISTRICT_CHOICES  # Make sure DISTRICT_CHOICES exists

def property_list(request):
    properties = Property.objects.all()

    # Get filter parameters
    district = request.GET.get('district')
    max_rent = request.GET.get('max_rent')
    bedrooms = request.GET.get('bedrooms')
    property_type = request.GET.get('property_type')
    q = request.GET.get('q')  # optional search query

    # Apply filters
    if district and district != "all":  # ignore 'all'
        properties = properties.filter(district=district)
    if max_rent:
        properties = properties.filter(rent__lte=max_rent)
    if bedrooms:
        properties = properties.filter(bedrooms=bedrooms)
    if property_type:
        properties = properties.filter(property_type=property_type)
    if q:
        properties = properties.filter(title__icontains=q)

    context = {
        'properties': properties,
        'DISTRICTS': DISTRICT_CHOICES,
    }
    return render(request, 'rentalapp/property_list.html', context)


