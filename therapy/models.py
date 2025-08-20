from django.contrib.auth.models import Permission, Group
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from clinic.models import Clinic
from users.models import User, Role


# Therapist Profile
class TherapistProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # Add clinic relationship
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='therapists'
    )

    # Link to User model (created automatically)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='therapist_profile'
    )

    class Meta:
        verbose_name = 'Therapist'
        verbose_name_plural = 'Therapists'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Parent Profile
class ParentProfile(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Link to User model (created automatically)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parent_profile'
    )

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Child Model
class Child(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='children'
    )
    assigned_therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.clinic.name})"


class Goal(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    is_long_term = models.BooleanField(default=False)


class Task(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    title = models.TextField()
    difficulty = models.CharField(max_length=20, choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'),
                                                          ('advanced', 'Advanced')])


class Assignment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='assignments')
    therapist = models.ForeignKey(TherapistProfile, on_delete=models.CASCADE, related_name='assignments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task.title} assigned to {self.child.name} by {self.therapist.first_name} {self.therapist.last_name}"


# SIGNAL HANDLERS FOR AUTOMATIC USER CREATION
@receiver(post_save, sender=TherapistProfile)
def create_therapist_user(sender, instance, created, **kwargs):
    """Automatically create User account when TherapistProfile is created"""
    if created and instance.email and not instance.user:
        try:
            # Get or create Therapist role
            therapist_role, _ = Role.objects.get_or_create(name='Therapist')

            # Create user account
            user = User.objects.create(
                email=instance.email,
                first_name=instance.first_name,
                last_name=instance.last_name,
                role=therapist_role,
                is_staff=True,  # Therapists can access admin
                is_active=instance.is_active,
                password_reset_required=True
            )

            # Generate temporary password
            temp_password = user.generate_temp_password()
            user.save()

            # Assign to therapist group and permissions
            therapist_group, _ = Group.objects.get_or_create(name='therapist')
            user.groups.add(therapist_group)

            # Add specific permissions
            permissions = [
                'add_assignment', 'change_assignment', 'view_assignment',
                'add_goal', 'change_goal', 'view_goal',
                'add_task', 'change_task', 'view_task',
                'view_child', 'change_child',
            ]

            for codename in permissions:
                try:
                    perm = Permission.objects.get(codename=codename)
                    user.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    print(f"Permission {codename} not found")

            # Link user to therapist profile
            instance.user = user
            instance.save(update_fields=['user'])

            # Send welcome email
            send_therapist_welcome_email(instance, temp_password)

        except Exception as e:
            print(f"Error creating therapist user: {e}")





@receiver(post_save, sender=ParentProfile)
def create_parent_user(sender, instance, created, **kwargs):
    """Automatically create User account when ParentProfile is created"""
    if created and instance.parent_email and not instance.user:
        try:
            # Get or create Parent role
            parent_role, _ = Role.objects.get_or_create(name='Parent')

            # Create user account
            user = User.objects.create(
                email=instance.parent_email,
                first_name=instance.first_name,
                last_name=instance.last_name,
                role=parent_role,
                is_staff=False,  # Parents don't need admin access initially
                is_active=instance.is_active,
                password_reset_required=True
            )

            # Generate temporary password
            temp_password = user.generate_temp_password()
            user.save()

            # Assign to parent group
            user.assign_to_group('parent')

            # Link user to parent profile
            instance.user = user
            instance.save(update_fields=['user'])

            # Send welcome email
            send_parent_welcome_email(instance, temp_password)

        except Exception as e:
            print(f"Error creating parent user: {e}")


def send_therapist_welcome_email(therapist, temp_password):
    """Send welcome email to new therapist"""
    subject = 'Welcome to Neuvii - Therapist Account Created'

    reset_link = f"http://127.0.0.1:8000/auth/reset-password/?email={therapist.email}&temp_password={temp_password}"

    message = f"""
Welcome to Neuvii, {therapist.first_name}!

Your therapist account has been created successfully. Here are your login details:

Email: {therapist.email}
Temporary Password: {temp_password}

Please click the link below to set your new password:
{reset_link}

Alternatively, you can login at: http://127.0.0.1:8000/auth/login/

IMPORTANT: You will be required to change your password upon first login for security reasons.

As a therapist, you'll have access to:
- Manage your assigned clients and children
- Create and track therapy goals and tasks
- Generate progress reports
- Communicate with parents

If you have any questions, please contact our support team.

Best regards,
Neuvii Team
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [therapist.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send therapist welcome email: {e}")


def send_parent_welcome_email(parent, temp_password):
    """Send welcome email to new parent"""
    subject = 'Welcome to Neuvii - Parent Account Created'

    reset_link = f"http://127.0.0.1:8000/auth/reset-password/?email={parent.parent_email}&temp_password={temp_password}"

    message = f"""
Welcome to Neuvii, {parent.first_name}!

Your parent account has been created successfully. Here are your login details:

Email: {parent.parent_email}  
Temporary Password: {temp_password}

Please click the link below to set your new password:
{reset_link}

Alternatively, you can login at: http://127.0.0.1:8000/auth/login/

IMPORTANT: You will be required to change your password upon first login for security reasons.

As a parent, you'll be able to:
- View your child's therapy progress
- Track completed assignments and goals
- Communicate with therapists
- Access progress reports

If you have any questions, please contact our support team.

Best regards,
Neuvii Team
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [parent.parent_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send parent welcome email: {e}")