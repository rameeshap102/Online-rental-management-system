from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from .models import Property
from .models import Booking
from .models import Maintenance
from django.contrib.auth import get_user_model

# =========================
# ✅ User Signup / Registration Form
# =========================
class CustomUserCreationForm(UserCreationForm):
    # Full name field for display
    full_name = forms.CharField(max_length=100, required=True)
    
    # Country code for phone number
    country_code = forms.ChoiceField(
        choices=[("+91", "+91 (India)"), ("+1", "+1 (USA)"), ("+44", "+44 (UK)")],
        required=True,
        initial="+91"
    )
    
    # Phone number input
    phone_number = forms.CharField(max_length=15, required=True)
    
    # Role selection: tenant or landlord
    role = forms.ChoiceField(  # ✅ match with template
        choices=[("tenant", "Tenant"), ("landlord", "Landlord")],
        required=True,
        widget=forms.RadioSelect
    )

    class Meta:
        model = CustomUser
        fields = ["full_name", "email", "country_code", "phone_number", "role", "password1", "password2"]

    # ✅ Override password validation to just match passwords
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2
    
    # Save user instance with proper phone format and role
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get("email")  # ✅ auto-fill username with email
        user.phone_number = f"{self.cleaned_data['country_code']}{self.cleaned_data['phone_number']}"  # combine country code
        user.full_name = self.cleaned_data["full_name"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user

# =========================
# ✅ Email-based Login Form
# =========================
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "class": "form-control"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    # Override clean to authenticate using email
    def clean(self):
        email = self.cleaned_data.get("username")  # Django expects 'username', mapped to email
        password = self.cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid email or password.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("This account is inactive.")
        return self.cleaned_data

# =========================
# ✅ Property Form for Landlords
# =========================
class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ['owner']  # Owner is assigned in views
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rent': forms.NumberInput(attrs={'class': 'form-control'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'size': forms.NumberInput(attrs={'class': 'form-control'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# =========================
# ✅ Booking Form for Tenants
# =========================
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

# =========================
# ✅ Maintenance Form for Tenants
# =========================
User = get_user_model()

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ["issue", "category"]  # tenant should not pick property or status
        widgets = {
            "issue": forms.Textarea(attrs={"rows":4, "class":"form-control", "placeholder":"Describe the issue..."})
        }

# =========================
# ✅ Profile Form (basic editable fields)
# =========================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]  # add other editable fields as needed
        widgets = {
            "first_name": forms.TextInput(attrs={"class":"form-control"}),
            "last_name": forms.TextInput(attrs={"class":"form-control"}),
            "email": forms.EmailInput(attrs={"class":"form-control"}),
        }

# =========================
# ✅ Edit Profile Form (detailed)
# =========================
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "address", "district"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "district": forms.Select(attrs={"class": "form-control"}),
        }
