from django.contrib import admin
from django import forms
from django.contrib import messages
from django.core.validators import RegexValidator
from django.template import TemplateDoesNotExist
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from .models import Clinic
from users.models import Role, User
import secrets
import string


def generate_temp_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            return password


class ClinicForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = '__all__'
        widgets = {
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
            'address_line_1': forms.TextInput(attrs={'class': 'wide-input'}),
            'address_line_2': forms.TextInput(attrs={'class': 'wide-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'clinic_admin' in self.fields:
            self.fields['clinic_admin'].widget = forms.HiddenInput()

        # Make email required for new clinic
        if not self.instance.pk:  # New clinic
            self.fields['email'].required = True
            self.fields['contact_person_name'].required = True

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        contact_person_name = cleaned_data.get('contact_person_name')

        if not self.instance.pk:  # Only for new clinic
            if not email:
                raise forms.ValidationError("Email is required to create clinic admin account.")
            if not contact_person_name:
                raise forms.ValidationError("Contact person name is required to create clinic admin account.")

            # Check if email is already in use
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(f"Email {email} is already registered.")

        return cleaned_data


class ClinicAdmin(admin.ModelAdmin):
    form = ClinicForm
    list_display = [
        'id', 'name', 'contact_person_name', 'email',
        'clinic_admin_status', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'license_status']
    search_fields = ['name', 'contact_person_name', 'email']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Clinic Information', {
            'fields': (
                'name',
                ('address_line_1', 'address_line_2'),
                ('city', 'country'),
            ),
        }),
        ('Primary Contact Information', {
            'fields': (
                ('contact_person_name', 'role'),
                'email',
            ),
            'description': 'Email and contact person name are required to create admin account automatically'
        }),
        ('Status & Compliance', {
            'fields': (
                'is_active',
                ('agreement_signed', 'license_status'),
                'consent_template',
            ),
        }),
        ('Branding', {
            'fields': ('logo',),
            'classes': ('collapse',),
        }),
        ('Internal Information', {
            'fields': ('internal_notes',),
            'classes': ('collapse',),
            'description': 'Visible to Neuvii Admin only'
        }),
        ('System Information', {
            'fields': ('clinic_admin', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Auto-generated fields'
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def has_module_permission(self, request):
        """Allow both Neuvii Admin and Clinic Admin to access"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Neuvii Admin', 'Clinic Admin']
        return False

    def has_view_permission(self, request, obj=None):
        """Control view permission"""
        if not self.has_module_permission(request):
            return False

        # Neuvii Admin can view all clinics - FULL ACCESS
        if request.user.role and request.user.role.name == 'Neuvii Admin':
            return True

        # Clinic Admin can only view their own clinic
        if request.user.role and request.user.role.name == 'Clinic Admin':
            if obj is None:  # List view
                return True
            # Check if this is their clinic
            if hasattr(request.user, 'clinic_admin'):
                return obj == request.user.clinic_admin

        return False

    def has_add_permission(self, request):
        """Only Neuvii Admin can add new clinics"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Neuvii Admin has FULL permission to add clinics
        return request.user.role and request.user.role.name == 'Neuvii Admin'

    def has_change_permission(self, request, obj=None):
        """Control change permission"""
        if not self.has_module_permission(request):
            return False

        # Neuvii Admin can change all clinics - FULL ACCESS
        if request.user.role and request.user.role.name == 'Neuvii Admin':
            return True

        # Clinic Admin can change limited fields of their own clinic
        if request.user.role and request.user.role.name == 'Clinic Admin':
            if obj is None:
                return True
            if hasattr(request.user, 'clinic_admin'):
                return obj == request.user.clinic_admin

        return False

    def has_delete_permission(self, request, obj=None):
        """Only Neuvii Admin can delete clinics"""
        if not self.has_module_permission(request):
            return False
        # Neuvii Admin has FULL permission to delete clinics
        return request.user.role and request.user.role.name == 'Neuvii Admin'

    def get_queryset(self, request):
        """Filter queryset based on user role"""
        qs = super().get_queryset(request)

        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        # Neuvii Admin sees ALL clinics - FULL ACCESS
        if request.user.is_superuser or request.user.role.name == 'Neuvii Admin':
            return qs
        elif request.user.role.name == 'Clinic Admin':
            # Show only their own clinic
            if hasattr(request.user, 'clinic_admin'):
                return qs.filter(id=request.user.clinic_admin.id)

        return qs.none()

    def save_model(self, request, obj, form, change):
        """Handle clinic creation and admin user creation"""
        if not change and obj.email and obj.contact_person_name:
            try:
                # Get or create Clinic Admin role
                clinic_admin_role, created = Role.objects.get_or_create(
                    name='Clinic Admin',
                    defaults={'name': 'Clinic Admin'}
                )

                # Generate secure password
                temp_password = generate_temp_password()

                # Parse name
                name_parts = obj.contact_person_name.strip().split()
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                # Create user with staff status
                user = User.objects.create_user(
                    email=obj.email,
                    password=temp_password,
                    first_name=first_name,
                    last_name=last_name,
                    role=clinic_admin_role,
                    is_staff=True,  # Required for admin access
                    is_active=True,
                    password_reset_required=True  # Force password change on first login
                )

                # Add user to Clinic Admin group
                clinic_admin_group, _ = Group.objects.get_or_create(name='Clinic Admin')
                user.groups.add(clinic_admin_group)

                # Set clinic admin permissions
                permissions = [
                    'add_therapistprofile', 'change_therapistprofile', 'view_therapistprofile',
                    'add_parentprofile', 'change_parentprofile', 'view_parentprofile',
                    'add_child', 'change_child', 'view_child',
                    'view_clinic', 'change_clinic',
                ]

                for codename in permissions:
                    try:
                        perm = Permission.objects.get(codename=codename)
                        user.user_permissions.add(perm)
                    except Permission.DoesNotExist:
                        messages.warning(
                            request,
                            f"Permission {codename} not found"
                        )

                # Link user to clinic
                obj.clinic_admin = user

                # Save clinic
                super().save_model(request, obj, form, change)

                # Send welcome email
                self.send_welcome_email(request, obj, temp_password)

                messages.success(
                    request,
                    f'Created clinic admin account for {obj.email}. '
                    f'Welcome email sent with login credentials.'
                )

            except Exception as e:
                messages.error(
                    request,
                    f'Error creating clinic admin: {str(e)}'
                )
                raise
        else:
            super().save_model(request, obj, form, change)

    def send_welcome_email(self, request, clinic, temp_password):
        """Send welcome email to new clinic admin"""
        try:
            # Generate reset password URL
            reset_url = request.build_absolute_uri(
                f'/auth/reset-password/?email={clinic.email}&temp_password={temp_password}'
            )

            context = {
                'clinic_name': clinic.name,
                'contact_name': clinic.contact_person_name,
                'email': clinic.email,
                'temp_password': temp_password,
                'reset_url': reset_url,
                'login_url': request.build_absolute_uri('/admin/')
            }

            subject = f'Welcome to Neuvii - {clinic.name} Admin Account'

            # Simple text message if template doesn't exist
            message = f"""
Welcome to Neuvii!

Your clinic admin account has been created for {clinic.name}.

Login Details:
Email: {clinic.email}
Temporary Password: {temp_password}

Please visit: {reset_url}
Or login at: {context['login_url']}

You will be required to change your password on first login.

Best regards,
Neuvii Team
            """

            try:
                html_message = render_to_string('clinic/emails/welcome_email.html', context)
            except:
                html_message = None

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[clinic.email],
                html_message=html_message,
                fail_silently=False,
            )

            return True

        except Exception as e:
            messages.error(
                request,
                f'Failed to send welcome email: {str(e)}'
            )
            return False

    def clinic_admin_status(self, obj):
        """Show clinic admin status with link to user"""
        if obj.clinic_admin:
            url = reverse('admin:users_user_change', args=[obj.clinic_admin.id])
            return format_html(
                '<span style="color: green;">✓</span> '
                '<a href="{}">{}</a>',
                url, obj.clinic_admin.get_full_name() or obj.clinic_admin.email
            )
        return format_html('<span style="color: red;">✗</span> No admin user')

    clinic_admin_status.short_description = "Admin Account"

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on user role"""
        readonly_fields = list(self.readonly_fields)

        if obj:  # Editing existing object
            readonly_fields.extend(['clinic_admin'])

            # Clinic Admin has limited edit permissions
            if request.user.role and request.user.role.name == 'Clinic Admin':
                readonly_fields.extend([
                    'is_active', 'license_status', 'agreement_signed',
                    'internal_notes', 'email', 'contact_person_name'
                ])
            # Neuvii Admin has NO readonly restrictions - FULL ACCESS
            elif request.user.role and request.user.role.name == 'Neuvii Admin':
                # Remove restrictions - Neuvii Admin can edit everything
                pass

        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on user role"""
        fieldsets = list(self.fieldsets)

        # Hide internal notes from Clinic Admin only
        if request.user.role and request.user.role.name == 'Clinic Admin':
            # Remove Internal Information fieldset for clinic admin
            fieldsets = [fs for fs in fieldsets if fs[0] != 'Internal Information']
        # Neuvii Admin sees ALL fieldsets - FULL ACCESS

        return fieldsets

    class Media:
        css = {
            'all': ('admin/css/clinic_admin.css',)
        }