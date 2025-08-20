from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib import messages
from datetime import datetime

class NeuviiAdminSite(AdminSite):
    """
    Custom admin site for Neuvii with role-based access control
    """
    site_header = "Neuvii Therapy Management System"
    site_title = "Neuvii Admin Portal"
    index_title = "Administration Dashboard"

    def get_app_list(self, request, app_label=None):
        """
        Customize the admin index page app list based on user role
        """
        app_list = super().get_app_list(request, app_label)

        if not request.user.is_authenticated or not request.user.role:
            return app_list

        role_name = request.user.role.name.lower()

        # Restructure app list based on role
        if role_name == 'neuvii admin':
            return self.get_neuvii_admin_apps(app_list, request)
        elif role_name == 'clinic admin':
            return self.get_clinic_admin_apps(app_list, request)
        elif role_name == 'therapist':
            return self.get_therapist_apps(app_list, request)
        elif role_name == 'parent':
            return self.get_parent_apps(app_list, request)

        return app_list

    def get_neuvii_admin_apps(self, app_list, request):
        """Full access for Neuvii Admin with properly structured sidebar"""
        custom_apps = []

        # 1. Clinic Management Section
        clinic_models = []
        for app in app_list:
            if app['app_label'] == 'clinic':
                for model in app['models']:
                    if model['object_name'] == 'Clinic':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Clinics'
                        clinic_models.append(model)

        if clinic_models:
            custom_apps.append({
                'name': 'Clinic Management',
                'app_label': 'clinic',
                'app_url': reverse('admin:app_list', kwargs={'app_label': 'clinic'}),
                'has_module_perms': True,
                'models': clinic_models
            })

        # 2. Therapy Management Section (Therapists)
        therapy_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'TherapistProfile':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Therapies'
                        therapy_models.append(model)

        if therapy_models:
            custom_apps.append({
                'name': 'Therapy Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_therapistprofile_changelist'),
                'has_module_perms': True,
                'models': therapy_models
            })

        # 3. Client Management Section (Parents)
        client_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'ParentProfile':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Clients'
                        client_models.append(model)

        if client_models:
            custom_apps.append({
                'name': 'Client Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_parentprofile_changelist'),
                'has_module_perms': True,
                'models': client_models
            })

        # 4. Child Management Section
        child_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Child':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Children'
                        child_models.append(model)

        if child_models:
            custom_apps.append({
                'name': 'Child Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_child_changelist'),
                'has_module_perms': True,
                'models': child_models
            })

        # 5. Assignment Management Section
        assignment_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Assignment':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Assignments'
                        assignment_models.append(model)

        if assignment_models:
            custom_apps.append({
                'name': 'Assignment Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_assignment_changelist'),
                'has_module_perms': True,
                'models': assignment_models
            })

        # 6. Goal Management Section
        goal_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Goal':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Goals'
                        goal_models.append(model)

        if goal_models:
            custom_apps.append({
                'name': 'Goal Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_goal_changelist'),
                'has_module_perms': True,
                'models': goal_models
            })

        # 7. Task Management Section
        task_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Task':
                        # Ensure full CRUD permissions for Neuvii Admin
                        model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        # Rename for sidebar display
                        model['name'] = 'Tasks'
                        task_models.append(model)

        if task_models:
            custom_apps.append({
                'name': 'Task Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_task_changelist'),
                'has_module_perms': True,
                'models': task_models
            })

        # Filter out empty apps and return
        return [app for app in custom_apps if app.get('models')]

    def get_clinic_admin_apps(self, app_list, request):
        """Restricted access for Clinic Admin"""
        allowed_apps = []

        # Get the clinic admin's clinic
        clinic = None
        if hasattr(request.user, 'clinic_admin'):
            clinic = request.user.clinic_admin

        # 1. Clinic Management Section (View Only)
        clinic_models = []
        for app in app_list:
            if app['app_label'] == 'clinic':
                for model in app['models']:
                    if model['object_name'] == 'Clinic':
                        # Customize permissions for clinic admin
                        clinic_model = model.copy()
                        clinic_model['perms'] = {
                            'add': False,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        clinic_model['name'] = 'Clinics'
                        if clinic:
                            clinic_model['admin_url'] = reverse('admin:clinic_clinic_change', args=[clinic.id])
                        clinic_models.append(clinic_model)

        if clinic_models:
            allowed_apps.append({
                'name': 'Clinic Management',
                'app_label': 'clinic',
                'app_url': reverse('admin:app_list', kwargs={'app_label': 'clinic'}),
                'has_module_perms': True,
                'models': clinic_models
            })

        # 2. Therapy Management Section
        therapy_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'TherapistProfile':
                        therapy_model = model.copy()
                        therapy_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        therapy_model['name'] = 'Therapies'
                        therapy_models.append(therapy_model)

        if therapy_models:
            allowed_apps.append({
                'name': 'Therapy Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_therapistprofile_changelist'),
                'has_module_perms': True,
                'models': therapy_models
            })

        # 3. Client Management Section
        client_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'ParentProfile':
                        client_model = model.copy()
                        client_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        client_model['name'] = 'Clients'
                        client_models.append(client_model)

        if client_models:
            allowed_apps.append({
                'name': 'Client Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_parentprofile_changelist'),
                'has_module_perms': True,
                'models': client_models
            })

        # 4. Child Management Section
        child_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Child':
                        child_model = model.copy()
                        child_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        child_model['name'] = 'Children'
                        child_models.append(child_model)

        if child_models:
            allowed_apps.append({
                'name': 'Child Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_child_changelist'),
                'has_module_perms': True,
                'models': child_models
            })

        # 5. Assignment Management Section
        assignment_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Assignment':
                        assignment_model = model.copy()
                        assignment_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        assignment_model['name'] = 'Assignments'
                        assignment_models.append(assignment_model)

        if assignment_models:
            allowed_apps.append({
                'name': 'Assignment Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_assignment_changelist'),
                'has_module_perms': True,
                'models': assignment_models
            })

        # 6. Goal Management Section
        goal_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Goal':
                        goal_model = model.copy()
                        goal_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        goal_model['name'] = 'Goals'
                        goal_models.append(goal_model)

        if goal_models:
            allowed_apps.append({
                'name': 'Goal Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_goal_changelist'),
                'has_module_perms': True,
                'models': goal_models
            })

        # 7. Task Management Section
        task_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Task':
                        task_model = model.copy()
                        task_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        task_model['name'] = 'Tasks'
                        task_models.append(task_model)

        if task_models:
            allowed_apps.append({
                'name': 'Task Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_task_changelist'),
                'has_module_perms': True,
                'models': task_models
            })

        return allowed_apps

    def get_therapist_apps(self, app_list, request):
        """Restricted access for Therapists"""
        allowed_apps = []

        # Child Management Section (Only assigned children)
        child_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Child':
                        child_model = model.copy()
                        child_model['perms'] = {
                            'add': False,
                            'change': True,
                            'delete': False,
                            'view': True
                        }
                        child_model['name'] = 'Children'
                        child_models.append(child_model)

        if child_models:
            allowed_apps.append({
                'name': 'Child Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_child_changelist'),
                'has_module_perms': True,
                'models': child_models
            })

        # Assignment Management Section
        assignment_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Assignment':
                        assignment_model = model.copy()
                        assignment_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        assignment_model['name'] = 'Assignments'
                        assignment_models.append(assignment_model)

        if assignment_models:
            allowed_apps.append({
                'name': 'Assignment Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_assignment_changelist'),
                'has_module_perms': True,
                'models': assignment_models
            })

        # Goal Management Section
        goal_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Goal':
                        goal_model = model.copy()
                        goal_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        goal_model['name'] = 'Goals'
                        goal_models.append(goal_model)

        if goal_models:
            allowed_apps.append({
                'name': 'Goal Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_goal_changelist'),
                'has_module_perms': True,
                'models': goal_models
            })

        # Task Management Section
        task_models = []
        case_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Task':
                        case_model = model.copy()
                        case_model['perms'] = {
                            'add': True,
                            'change': True,
                            'delete': True,
                            'view': True
                        }
                        case_model['name'] = 'Tasks'
                        case_models.append(case_model)

        if case_models:
            allowed_apps.append({
                'name': 'Task Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_task_changelist'),
                'has_module_perms': True,
                'models': case_models
            })

        return allowed_apps

    def get_parent_apps(self, app_list, request):
        """Restricted access for Parents"""
        allowed_apps = []

        # Child Management Section (Only their children)
        child_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Child':
                        child_model = model.copy()
                        child_model['perms'] = {
                            'add': False,
                            'change': False,
                            'delete': False,
                            'view': True
                        }
                        child_model['name'] = 'Children'
                        child_models.append(child_model)

        if child_models:
            allowed_apps.append({
                'name': 'Child Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_child_changelist'),
                'has_module_perms': True,
                'models': child_models
            })

        # Assignment Management Section (Only their children's assignments)
        assignment_models = []
        for app in app_list:
            if app['app_label'] == 'therapy':
                for model in app['models']:
                    if model['object_name'] == 'Assignment':
                        assignment_model = model.copy()
                        assignment_model['perms'] = {
                            'add': False,
                            'change': True,  # Can mark assignments complete
                            'delete': False,
                            'view': True
                        }
                        assignment_model['name'] = 'Assignments'
                        assignment_models.append(assignment_model)

        if assignment_models:
            allowed_apps.append({
                'name': 'Assignment Management',
                'app_label': 'therapy',
                'app_url': reverse('admin:therapy_assignment_changelist'),
                'has_module_perms': True,
                'models': assignment_models
            })

        return allowed_apps

    def index(self, request, extra_context=None):
        """Customize the admin index page"""
        if not request.user.is_authenticated:
            return self.login(request)

        context = {
            'title': self.index_title,
            'subtitle': None,
            'current_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        }

        if request.user.role:
            role_name = request.user.role.name
            context.update({
                'user_role': role_name,
                'subtitle': f"{role_name} Dashboard",
            })

            if role_name == 'Neuvii Admin':
                from clinic.models import Clinic
                from therapy.models import TherapistProfile, ParentProfile, Child
                context.update({
                    'total_clinics': Clinic.objects.count(),
                    'active_clinics': Clinic.objects.filter(is_active=True).count(),
                    'total_therapists': TherapistProfile.objects.count(),
                    'total_clients': ParentProfile.objects.count(),
                    'total_children': Child.objects.count(),
                })
            elif role_name == 'Clinic Admin':
                if hasattr(request.user, 'clinic_admin'):
                    clinic = request.user.clinic_admin
                    from therapy.models import TherapistProfile, ParentProfile, Child
                    context.update({
                        'clinic_name': clinic.name,
                        'clinic_therapists': TherapistProfile.objects.filter(clinic=clinic).count(),
                        'clinic_children': Child.objects.filter(clinic=clinic).count(),
                    })

        if extra_context:
            context.update(extra_context)

        return super().index(request, context)

# Create the custom admin site instance
neuvii_admin_site = NeuviiAdminSite(name='neuvii_admin')

# Register your models with the custom admin site
# Import admin classes
from clinic.admin import ClinicAdmin
from clinic.models import Clinic
from users.admin import CustomUserAdmin, RoleAdmin, GroupAdmin
from users.models import User, Role
from django.contrib.auth.models import Group
from therapy.admin import TherapistProfileAdmin, ParentProfileAdmin, ChildAdmin, AssignmentAdmin, GoalAdmin, TaskAdmin
from therapy.models import TherapistProfile, ParentProfile, Child, Assignment, Goal, Task

# Register models with the custom admin site
neuvii_admin_site.register(User, CustomUserAdmin)
neuvii_admin_site.register(Role, RoleAdmin)
neuvii_admin_site.register(Group, GroupAdmin)
neuvii_admin_site.register(Clinic, ClinicAdmin)
neuvii_admin_site.register(TherapistProfile, TherapistProfileAdmin)
neuvii_admin_site.register(ParentProfile, ParentProfileAdmin)
neuvii_admin_site.register(Child, ChildAdmin)
neuvii_admin_site.register(Assignment, AssignmentAdmin)
neuvii_admin_site.register(Goal, GoalAdmin)
neuvii_admin_site.register(Task, TaskAdmin)