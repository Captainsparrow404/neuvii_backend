from django.contrib import admin
from django.core.exceptions import PermissionDenied


class RoleBasedAdminMixin:
    """Base mixin for role-based admin access control"""
    allowed_roles = []

    def has_module_permission(self, request):
        """Check if user has permission to access the module"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not self.allowed_roles:
            return super().has_module_permission(request)
        if hasattr(request.user, "role") and request.user.role:
            return request.user.role.name in self.allowed_roles
        return False

    def has_view_permission(self, request, obj=None):
        """Check if user can view objects"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not self.has_module_permission(request):
            return False
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        """Check if user can add objects"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not self.has_module_permission(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """Check if user can change objects"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not self.has_module_permission(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete objects"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not self.has_module_permission(request):
            return False
        return super().has_delete_permission(request, obj)


class NeuviiAdminMixin(RoleBasedAdminMixin):
    """Mixin for Neuvii Admin - FULL CRUD access"""
    allowed_roles = ['Neuvii Admin']

    def has_view_permission(self, request, obj=None):
        """Neuvii Admin has FULL view permission"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full access
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        """Neuvii Admin has FULL add permission"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full access
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """Neuvii Admin has FULL change permission"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full access
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Neuvii Admin has FULL delete permission"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full access
        return super().has_delete_permission(request, obj)


class ClinicAdminMixin(RoleBasedAdminMixin):
    """Mixin for Clinic Admin and above access"""
    allowed_roles = ['Neuvii Admin', 'Clinic Admin']

    def has_add_permission(self, request):
        """Control add permission based on role"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Neuvii Admin has full permission
            if request.user.role.name == 'Neuvii Admin':
                return True
            # Clinic Admin has limited permission
            elif request.user.role.name == 'Clinic Admin':
                return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Neuvii Admin can delete in most cases"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Only Neuvii Admin can delete
            return request.user.role.name == 'Neuvii Admin'
        return False


class TherapistAccessMixin(RoleBasedAdminMixin):
    """Mixin for Therapist and above access"""
    allowed_roles = ['Neuvii Admin', 'Clinic Admin', 'Therapist']

    def has_add_permission(self, request):
        """Control add permission for therapists"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Neuvii Admin has full permission
            if request.user.role.name == 'Neuvii Admin':
                return True
            # Clinic Admin and Therapist have limited permission
            elif request.user.role.name in ['Clinic Admin', 'Therapist']:
                return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Neuvii Admin can delete"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Only Neuvii Admin can delete
            return request.user.role.name == 'Neuvii Admin'
        return False


class ParentAccessMixin(RoleBasedAdminMixin):
    """Mixin for all authenticated users including parents"""
    allowed_roles = ['Neuvii Admin', 'Clinic Admin', 'Therapist', 'Parent']

    def has_add_permission(self, request):
        """Parents cannot add, others based on role"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Neuvii Admin has full permission
            if request.user.role.name == 'Neuvii Admin':
                return True
            # Clinic Admin and Therapist can add
            elif request.user.role.name in ['Clinic Admin', 'Therapist']:
                return True
            # Parents cannot add
            elif request.user.role.name == 'Parent':
                return False
        return False

    def has_change_permission(self, request, obj=None):
        """Control change permission based on role and ownership"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Neuvii Admin has full permission
            if request.user.role.name == 'Neuvii Admin':
                return True
            # Others have conditional permission
            elif request.user.role.name in ['Clinic Admin', 'Therapist']:
                return True
            # Parents can only change their own related records
            elif request.user.role.name == 'Parent':
                if obj and hasattr(obj, 'parent'):
                    return hasattr(request.user, 'parent_profile') and obj.parent == request.user.parent_profile
                return False
        return False

    def has_delete_permission(self, request, obj=None):
        """Only Neuvii Admin can delete"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "role") and request.user.role:
            # Only Neuvii Admin can delete
            return request.user.role.name == 'Neuvii Admin'
        return False


class TherapistDataMixin:
    """Mixin to filter data based on therapist assignments"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        if request.user.is_superuser:
            return qs
        if not hasattr(request.user, "role") or not request.user.role:
            return qs.none()

        user_role = request.user.role.name

        # Neuvii Admin sees everything - FULL ACCESS
        if user_role == 'Neuvii Admin':
            return qs
        elif user_role == 'Clinic Admin':
            # Clinic admin sees data from their clinic
            if hasattr(request.user, 'clinic_admin'):
                if hasattr(qs.model, 'clinic'):
                    return qs.filter(clinic=request.user.clinic_admin)
                elif hasattr(qs.model, 'assigned_therapist'):
                    return qs.filter(assigned_therapist__clinic=request.user.clinic_admin)
            return qs.none()
        elif user_role == 'Therapist':
            # Therapist sees only their assigned data
            if hasattr(request.user, 'therapist_profile'):
                if hasattr(qs.model, 'assigned_therapist'):
                    return qs.filter(assigned_therapist=request.user.therapist_profile)
                elif hasattr(qs.model, 'therapist'):
                    return qs.filter(therapist=request.user.therapist_profile)
            return qs.none()
        elif user_role == 'Parent':
            # Parent sees only their own data
            if hasattr(request.user, 'parent_profile'):
                if hasattr(qs.model, 'parent'):
                    return qs.filter(parent=request.user.parent_profile)
                elif hasattr(qs.model, 'child'):
                    return qs.filter(child__parent=request.user.parent_profile)
            return qs.none()
        return qs.none()


class ParentDataMixin:
    """Mixin to filter data for parent access"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        if request.user.is_superuser:
            return qs
        if not hasattr(request.user, "role") or not request.user.role:
            return qs.none()

        user_role = request.user.role.name

        # Neuvii Admin sees everything - FULL ACCESS
        if user_role == 'Neuvii Admin':
            return qs
        elif user_role == 'Clinic Admin':
            # Clinic admin sees data from their clinic
            if hasattr(request.user, 'clinic_admin'):
                if hasattr(qs.model, 'clinic'):
                    return qs.filter(clinic=request.user.clinic_admin)
                elif hasattr(qs.model, 'children'):
                    return qs.filter(children__clinic=request.user.clinic_admin).distinct()
            return qs.none()
        elif user_role == 'Therapist':
            # Therapist sees parents of their assigned children
            if hasattr(request.user, 'therapist_profile'):
                if hasattr(qs.model, 'children'):
                    return qs.filter(children__assigned_therapist=request.user.therapist_profile).distinct()
            return qs.none()
        elif user_role == 'Parent':
            # Parent sees only their own profile
            if hasattr(request.user, 'parent_profile'):
                return qs.filter(id=request.user.parent_profile.id)
            return qs.none()
        return qs.none()