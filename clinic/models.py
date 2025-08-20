from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import Group, Permission
import secrets
import string


class Clinic(models.Model):
    name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)  # e.g. Director
    email = models.EmailField(blank=True, null=True)
    clinic_admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinic_admin'
    )
    agreement_signed = models.BooleanField(default=False)
    consent_template = models.FileField(upload_to='clinic_docs/', blank=True, null=True)  # Fixed spelling
    license_status = models.CharField(max_length=50, choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
                                  blank=True, null=True)
    internal_notes = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='clinic_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def assign_admin(self, user):
        """
        Assign a user as clinic admin and set up their permissions
        """
        from users.models import Role

        # Set up clinic admin role
        clinic_admin_role, _ = Role.objects.get_or_create(name='Clinic Admin')
        user.role = clinic_admin_role
        user.is_staff = True
        user.save()

        # Add to clinic admin group
        clinic_admin_group, _ = Group.objects.get_or_create(name='Clinic Admin')
        user.groups.add(clinic_admin_group)

        # Grant specific permissions
        permissions = [
            'add_therapistprofile', 'change_therapistprofile', 'view_therapistprofile', 'delete_therapistprofile',
            'add_parentprofile', 'change_parentprofile', 'view_parentprofile', 'delete_parentprofile',
            'add_child', 'change_child', 'view_child', 'delete_child',
            'view_clinic', 'change_clinic',
            'view_assignment', 'change_assignment',
            'view_goal', 'change_goal',
            'view_task', 'change_task'
        ]

        for codename in permissions:
            try:
                perm = Permission.objects.get(codename=codename)
                user.user_permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"Permission {codename} not found")

        # Link user to clinic
        self.clinic_admin = user
        self.save()

    def add_therapist(self, therapist):
        """
        Add a therapist to the clinic
        """
        self.therapists.add(therapist)

    def remove_therapist(self, therapist):
        """
        Remove a therapist from the clinic
        """
        self.therapists.remove(therapist)

    def get_active_therapists(self):
        """
        Get all active therapists in the clinic
        """
        return self.therapists.filter(is_active=True)

    def get_active_children(self):
        """
        Get all active children in the clinic
        """
        return self.child_set.filter(assigned_therapist__is_active=True)


def generate_temp_password(length=12):
    """
    Generate a secure temporary password
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@receiver(post_save, sender=Clinic)
def create_clinic_admin_user(sender, instance, created, **kwargs):
    """
    Automatically create Clinic Admin user when Clinic is created
    """
    if created and instance.email and instance.contact_person_name and not instance.clinic_admin:
        try:
            from users.models import User, Role

            # Get or create Clinic Admin role
            clinic_admin_role, _ = Role.objects.get_or_create(name='Clinic Admin')

            # Parse contact person name
            name_parts = instance.contact_person_name.strip().split()
            first_name = name_parts[0] if name_parts else 'Admin'
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            # Generate temporary password
            temp_password = generate_temp_password()

            # Create user account
            user = User.objects.create_user(
                email=instance.email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name,
                role=clinic_admin_role,
                is_staff=True,  # Clinic admins need admin access
                is_active=instance.is_active,
                password_reset_required=True  # Force password change on first login
            )

            # Add user to Clinic Admin group and set permissions
            clinic_admin_group, _ = Group.objects.get_or_create(name='Clinic Admin')
            user.groups.add(clinic_admin_group)

            # Set clinic admin permissions
            permissions = [
                'add_therapistprofile', 'change_therapistprofile', 'view_therapistprofile',
                'add_parentprofile', 'change_parentprofile', 'view_parentprofile',
                'add_child', 'change_child', 'view_child',
                'view_clinic',  # Can view but not edit clinic
            ]

            for codename in permissions:
                try:
                    perm = Permission.objects.get(codename=codename)
                    user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    print(f"Permission {codename} not found")

            # Link user to clinic
            instance.clinic_admin = user
            instance.save(update_fields=['clinic_admin'])

            # Send welcome email
            send_clinic_admin_welcome_email(instance, temp_password)

        except Exception as e:
            print(f"Error creating clinic admin user: {e}")


def send_clinic_admin_welcome_email(clinic, temp_password):
    """
    Send welcome email to new clinic admin
    """
    subject = f'Welcome to {clinic.name} - Your Admin Account'
    message = f"""
    Welcome to {clinic.name}!

    Your clinic admin account has been created. Here are your login details:

    Email: {clinic.email}
    Temporary Password: {temp_password}

    Please log in at {settings.SITE_URL}/admin/ and change your password.

    For security reasons, you will be required to change your password upon first login.

    If you have any questions, please contact support.
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [clinic.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending welcome email: {e}")