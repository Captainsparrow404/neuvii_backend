from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from neuvii_backend.admin_site import neuvii_admin_site

def redirect_to_login(request):
    return redirect('/auth/login/')

# Add custom admin configurations
def admin_context_processor(request):
    """Add role-based context to admin templates"""
    context = {}
    if request.user.is_authenticated and request.user.role:
        context.update({
            'user_role': request.user.role.name,
            'user_role_slug': request.user.role.name.lower().replace(' ', '_'),
            'is_neuvii_admin': request.user.role.name == 'Neuvii Admin',
            'is_clinic_admin': request.user.role.name == 'Clinic Admin',
            'is_therapist': request.user.role.name == 'Therapist',
            'is_parent': request.user.role.name == 'Parent',
        })
    return context

urlpatterns = [
    path("admin/", neuvii_admin_site.urls),  # Use our custom admin site
    path("auth/", include('users.urls')),
    path('', redirect_to_login),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)