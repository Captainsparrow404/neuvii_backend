from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Role, User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from neuvii_backend.admin_mixins import NeuviiAdminMixin


# Role Management - Only Neuvii Admin can manage roles
@admin.register(Role)
class RoleAdmin(NeuviiAdminMixin, admin.ModelAdmin):
    """Role management for Neuvii Admin only - FULL CRUD ACCESS"""
    list_display = ['id', 'name']
    search_fields = ['name']
    ordering = ['name']


# Unregister the default Group admin and register our custom one
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(NeuviiAdminMixin, admin.ModelAdmin):
    """Group management for Neuvii Admin only - FULL CRUD ACCESS"""
    list_display = ['name', 'user_count']
    search_fields = ['name']

    def user_count(self, obj):
        """Show number of users in group"""
        return obj.user_set.count()

    user_count.short_description = "Users"


# User model for admin - FULL CRUD for Neuvii Admin
@admin.register(User)
class CustomUserAdmin(NeuviiAdminMixin, UserAdmin):
    """
    Custom User Admin - FULL CRUD for Neuvii Admin only
    Users can be managed manually and are also created automatically via signals
    """
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ['id', 'email', 'get_full_name', 'role', 'is_active', 'password_reset_required', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'password_reset_required', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['id']

    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new users
            # Generate temporary password
            temp_password = obj.generate_temp_password()
            obj.password_reset_required = True

            # Save the user first
            super().save_model(request, obj, form, change)

            # Send email with temporary password
            self.send_welcome_email(obj, temp_password)

            messages.success(
                request,
                f'User {obj.email} created successfully. Welcome email sent with temporary password.'
            )
        else:
            super().save_model(request, obj, form, change)

    def send_welcome_email(self, user, temp_password):
        """Send welcome email with temporary password"""
        subject = 'Welcome to Neuvii - Your Account Details'

        # Create password reset link
        reset_link = f"http://127.0.0.1:8000/auth/reset-password/?email={user.email}&temp_password={temp_password}"

        message = f"""
Welcome to Neuvii!

Your account has been created successfully. Here are your login details:

Email: {user.email}
Temporary Password: {temp_password}

Please click the link below to set your new password:
{reset_link}

Alternatively, you can login at: http://127.0.0.1:8000/auth/login/

IMPORTANT: You will be required to change your password upon first login for security reasons.

If you have any questions, please contact our support team.

Best regards,
Neuvii Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")


# Custom admin site titles
admin.site.site_header = "Neuvii Administration"
admin.site.site_title = "Neuvii Admin Portal"
admin.site.index_title = "Welcome to Neuvii Administration"