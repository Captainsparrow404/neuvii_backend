from django.contrib.auth.models import Group, Permission
from users.models import User, Role
from therapy.models import TherapistProfile
from clinic.models import Clinic


def fix_permissions():
    # Fix therapist permissions
    therapist_role = Role.objects.get(name='Therapist')
    therapist_users = User.objects.filter(role=therapist_role)

    therapist_permissions = [
        'add_assignment', 'change_assignment', 'view_assignment',
        'add_goal', 'change_goal', 'view_goal',
        'add_task', 'change_task', 'view_task',
        'view_child', 'change_child',
    ]

    for user in therapist_users:
        user.is_staff = True
        user.save()

        therapist_group, _ = Group.objects.get_or_create(name='therapist')
        user.groups.add(therapist_group)

        for codename in therapist_permissions:
            try:
                perm = Permission.objects.get(codename=codename)
                user.user_permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"Permission {codename} not found")

    # Fix clinic admin permissions
    clinic_admin_role = Role.objects.get(name='Clinic Admin')
    clinic_admin_users = User.objects.filter(role=clinic_admin_role)

    clinic_admin_permissions = [
        'add_therapistprofile', 'change_therapistprofile', 'view_therapistprofile', 'delete_therapistprofile',
        'add_parentprofile', 'change_parentprofile', 'view_parentprofile', 'delete_parentprofile',
        'add_child', 'change_child', 'view_child', 'delete_child',
        'view_clinic', 'change_clinic',
        'view_assignment', 'change_assignment',
        'view_goal', 'change_goal',
        'view_task', 'change_task'
    ]

    for user in clinic_admin_users:
        user.is_staff = True
        user.save()

        clinic_admin_group, _ = Group.objects.get_or_create(name='Clinic Admin')
        user.groups.add(clinic_admin_group)

        for codename in clinic_admin_permissions:
            try:
                perm = Permission.objects.get(codename=codename)
                user.user_permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"Permission {codename} not found")


if __name__ == '__main__':
    fix_permissions()