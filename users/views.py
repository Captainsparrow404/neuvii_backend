from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import LoginForm, PasswordResetForm
from .models import User


@csrf_protect
@never_cache
def login_view(request):
    """Custom login view that handles role-based redirection"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request, request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Check if password reset is required
                    if user.password_reset_required:
                        return redirect('change_password')

                    return redirect_to_dashboard(request, user)
                else:
                    messages.error(request, 'Your account is disabled.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def redirect_to_dashboard(request, user):
    """
    Enhanced role-based redirection with custom admin views
    """
    if not user.role:
        return redirect('/admin/')  # Default admin if no role

    role_name = user.role.name.lower()

    # Role-based redirection with custom messaging
    if role_name == 'neuvii admin':
        messages.success(
            request,
            f"Welcome {user.get_full_name()}! You have full administrative access."
        )
        return redirect('/admin/')

    elif role_name == 'clinic admin':
        messages.success(
            request,
            f"Welcome {user.get_full_name()}! Managing clinic administration."
        )
        return redirect('/admin/')

    elif role_name == 'therapist':
        messages.success(
            request,
            f"Welcome {user.get_full_name()}! Access your therapy cases and assignments."
        )
        return redirect('/admin/')

    elif role_name == 'parent':
        messages.success(
            request,
            f"Welcome {user.get_full_name()}! View your children's therapy progress."
        )
        return redirect('/admin/')

    # Default fallback
    return redirect('/admin/')


@csrf_protect
def reset_password_view(request):
    """View to handle password reset for new users"""
    email = request.GET.get('email')
    temp_password = request.GET.get('temp_password')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            temp_password = request.POST.get('temp_password')
            new_password = form.cleaned_data['new_password']

            try:
                user = User.objects.get(email=email)
                # Verify temp password
                if user.check_password(temp_password):
                    user.set_password(new_password)
                    user.password_reset_required = False
                    user.save()

                    # Auto login user
                    login(request, user)

                    # Role-specific welcome message
                    role_messages = {
                        'Clinic Admin': 'You can now manage your clinic and its users.',
                        'Therapist': 'You can now access your therapy cases and create assignments.',
                        'Parent': 'You can now view your children\'s therapy progress and assignments.'
                    }

                    welcome_msg = role_messages.get(user.role.name, 'Welcome to Neuvii!')
                    messages.success(request, f'Password changed successfully! {welcome_msg}')

                    return redirect('admin:index')
                else:
                    messages.error(request, 'Invalid temporary password.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = PasswordResetForm()

    return render(request, 'auth/reset_password.html', {
        'form': form,
        'email': email,
        'temp_password': temp_password
    })


@login_required
def change_password_view(request):
    """View for users to change password after login"""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']

            request.user.set_password(new_password)
            request.user.password_reset_required = False

            # Auto-set is_staff=True for admin roles
            if request.user.role and request.user.role.name in ['Neuvii Admin', 'Clinic Admin', 'Therapist']:
                request.user.is_staff = True

            request.user.save()

            # Re-authenticate user with new password
            user = authenticate(request, username=request.user.email, password=new_password)
            login(request, user)

            # Role-specific success message
            role_messages = {
                'Neuvii Admin': 'You now have full system administration access.',
                'Clinic Admin': 'You can now manage your clinic and its users.',
                'Therapist': 'You can now access your therapy cases and create assignments.',
                'Parent': 'You can now view your children\'s therapy progress and assignments.'
            }

            welcome_msg = role_messages.get(request.user.role.name, 'Welcome to Neuvii!')
            messages.success(request, f'Password changed successfully! {welcome_msg}')

            return redirect_to_dashboard(request, request.user)
    else:
        form = PasswordResetForm()

    return render(request, 'auth/change_password.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    user_name = request.user.get_full_name() if request.user.is_authenticated else "User"
    logout(request)
    messages.success(request, f'Goodbye {user_name}! You have been logged out successfully.')
    return redirect('login')
