from functools import wraps
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def role_required(allowed_roles=[]):
    """
    Decorator to restrict access based on user roles.
    Usage:
        @role_required(['landlord'])
        def landlord_dashboard(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    f"❌ Access denied. This page is for {', '.join(allowed_roles)} only."
                )
                return render(request, "rentalapp/forbidden.html")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
