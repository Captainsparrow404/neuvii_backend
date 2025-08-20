from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
import secrets
import string


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    password_reset_required = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def generate_temp_password(self):
        """Generate a temporary password for new users"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        self.set_password(password)
        return password

    def get_role_display(self):
        return self.role.name if self.role else 'No Role'

    def assign_to_group(self, group_name):
        """Assign user to a Django Group"""
        try:
            group, created = Group.objects.get_or_create(name=group_name)
            self.groups.add(group)
            self.save()
        except Exception as e:
            print(f"Error assigning user to group {group_name}: {e}")

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"


@receiver(post_save, sender=User)
def create_user_groups(sender, instance, created, **kwargs):
    """Create default groups when first user is created"""
    if created:
        # Create default groups if they don't exist
        default_groups = ['neuvii_admin', 'clinic_admin', 'therapist', 'parent']
        for group_name in default_groups:
            Group.objects.get_or_create(name=group_name)


@receiver(post_save, sender=Role)
def create_roles_and_groups(sender, instance, created, **kwargs):
    """Ensure corresponding groups exist for each role"""
    if created:
        role_to_group = {
            'Neuvii Admin': 'neuvii_admin',
            'Clinic Admin': 'clinic_admin',
            'Therapist': 'therapist',
            'Parent': 'parent'
        }

        group_name = role_to_group.get(instance.name)
        if group_name:
            Group.objects.get_or_create(name=group_name)