# Create this file: neuvii_backend/admin_context.py

from django.conf import settings


def admin_context_processor(request):
    """Add role-based context variables for admin templates"""
    context = {
        'show_user_management': False,
        'show_clinic_management': False,
        'show_therapist_management': False,
        'show_client_management': False,
        'show_child_management': False,
        'show_therapy_management': False,
        'show_assignment_management': False,
        'can_add_clinics': False,
        'can_add_therapists': False,
        'can_add_clients': False,
    }

    if request.user.is_authenticated and request.user.role:
        role_name = request.user.role.name.lower()

        # Set context based on role
        context.update({
            'show_user_management': role_name == 'neuvii admin',
            'show_clinic_management': role_name in ['neuvii admin', 'clinic admin'],
            'show_therapist_management': role_name in ['neuvii admin', 'clinic admin'],
            'show_client_management': role_name in ['neuvii admin', 'clinic admin'],
            'show_child_management': role_name in ['neuvii admin', 'clinic admin', 'therapist', 'parent'],
            'show_therapy_management': role_name in ['neuvii admin', 'clinic admin', 'therapist'],
            'show_assignment_management': role_name in ['neuvii admin', 'clinic admin', 'therapist', 'parent'],

            # Permission levels
            'can_add_clinics': role_name == 'neuvii admin',
            'can_add_therapists': role_name in ['neuvii admin', 'clinic admin'],
            'can_add_clients': role_name in ['neuvii admin', 'clinic admin'],
        })

    return context


def get_dashboard_title(role_name):
    """Return role-specific dashboard title"""
    titles = {
        'Neuvii Admin': 'System Administration Dashboard',
        'Clinic Admin': 'Clinic Management Dashboard',
        'Therapist': 'Therapy Cases Dashboard',
        'Parent': 'Child Progress Dashboard'
    }
    return titles.get(role_name, 'Dashboard')


def get_welcome_message(role_name, user):
    """Return role-specific welcome message"""
    messages = {
        'Neuvii Admin': f'Welcome back, {user.first_name}! You have full system access.',
        'Clinic Admin': f'Welcome back, {user.first_name}! Manage your clinic effectively.',
        'Therapist': f'Welcome back, {user.first_name}! Ready to help your clients today?',
        'Parent': f'Welcome back, {user.first_name}! Check on your child\'s progress.'
    }
    return messages.get(role_name, f'Welcome back, {user.first_name}!')