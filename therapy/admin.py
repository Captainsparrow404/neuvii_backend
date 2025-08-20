from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from .models import TherapistProfile, ParentProfile, Child, Assignment, Goal, Task
from users.models import Role, User
from django import forms
from neuvii_backend.admin_mixins import (
    NeuviiAdminMixin, TherapistAccessMixin, ParentAccessMixin,
    TherapistDataMixin, ParentDataMixin
)


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from therapy.models import ParentProfile, TherapistProfile
        self.fields['parent'].queryset = ParentProfile.objects.all()
        self.fields['assigned_therapist'].queryset = TherapistProfile.objects.all()

        # Filter assigned_therapist based on clinic if instance has clinic
        if self.instance and self.instance.clinic:
            self.fields['assigned_therapist'].queryset = TherapistProfile.objects.filter(
                clinic=self.instance.clinic
            )


class TherapistProfileForm(forms.ModelForm):
    class Meta:
        model = TherapistProfile
        fields = '__all__'
        widgets = {
            'date_added': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the user field since it's auto-created
        if 'user' in self.fields:
            self.fields['user'].widget = forms.HiddenInput()


@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    form = TherapistProfileForm
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone_number',
                    'is_active', 'date_added', 'user_created', 'get_clinic']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    list_filter = ['is_active', 'date_added', 'clinic']
    readonly_fields = ['date_added', 'user']

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'is_active')
        }),
        ('Clinic Assignment', {
            'fields': ('clinic',),
        }),
        ('System Information', {
            'fields': ('user', 'date_added'),
            'classes': ('collapse',),
            'description': 'Auto-generated fields'
        })
    )

    def has_module_permission(self, request):
        """Allow Neuvii Admin full access, others limited"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Neuvii Admin', 'Clinic Admin', 'Therapist']
        return False

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        # Neuvii Admin can view all
        if request.user.role and request.user.role.name == 'Neuvii Admin':
            return True
        # Others have limited view
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        if not self.has_module_permission(request):
            return False
        # Only Neuvii Admin and Clinic Admin can add therapists
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            return request.user.role.name in ['Clinic Admin']
        return False

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        # Neuvii Admin has full permission
        if request.user.role and request.user.role.name == 'Neuvii Admin':
            return True
        # Others have limited permission
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Clinic Admin']
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        # Only Neuvii Admin can delete therapists
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name == 'Neuvii Admin'
        return False

    def get_clinic(self, obj):
        return obj.clinic.name if obj.clinic else '-'

    get_clinic.short_description = 'Clinic'

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user', 'clinic')
        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        user_role = request.user.role.name
        if user_role == 'Neuvii Admin':
            return qs  # Full access for Neuvii Admin
        elif user_role == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                return qs.filter(clinic=request.user.clinic_admin)
            return qs.none()
        elif user_role == 'Therapist':
            if hasattr(request.user, 'therapist_profile'):
                return qs.filter(id=request.user.therapist_profile.id)
            return qs.none()
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and obj.email:
            messages.info(request,
                          f"Creating therapist profile for {obj.first_name} {obj.last_name}. "
                          f"User account and welcome email will be sent to {obj.email}."
                          )

        # Auto-assign clinic for clinic admin
        if request.user.role and request.user.role.name == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                obj.clinic = request.user.clinic_admin

        super().save_model(request, obj, form, change)

        # Handle user creation feedback
        if obj.user:
            messages.success(request,
                             f"Therapist user account created successfully for {obj.email}. "
                             f"Welcome email sent with login credentials."
                             )
        elif not change and obj.email:
            messages.warning(request,
                             f"Therapist profile created but user account creation may have failed. "
                             f"Please check if {obj.email} is already registered."
                             )

    def user_created(self, obj):
        return "Yes" if obj.user else "No"

    user_created.short_description = "User Account"


class ParentProfileForm(forms.ModelForm):
    class Meta:
        model = ParentProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'user' in self.fields:
            self.fields['user'].widget = forms.HiddenInput()


class ChildInline(admin.TabularInline):
    """Inline for managing children within parent profile"""
    model = Child
    extra = 1
    fields = ('name', 'age', 'gender', 'assigned_therapist', 'clinic')
    autocomplete_fields = ['assigned_therapist']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_therapist":
            # Filter therapists based on clinic admin's clinic
            if hasattr(request.user, 'clinic_admin'):
                kwargs["queryset"] = TherapistProfile.objects.filter(
                    clinic=request.user.clinic_admin
                )
            elif request.user.role and request.user.role.name == 'Neuvii Admin':
                # Neuvii Admin sees all therapists
                kwargs["queryset"] = TherapistProfile.objects.all()

        if db_field.name == "clinic":
            # Auto-set clinic for clinic admin
            if hasattr(request.user, 'clinic_admin'):
                kwargs["queryset"] = kwargs.get("queryset",
                                                Child._meta.get_field('clinic').remote_field.model.objects).filter(
                    id=request.user.clinic_admin.id
                )
            elif request.user.role and request.user.role.name == 'Neuvii Admin':
                # Neuvii Admin sees all clinics
                kwargs["queryset"] = kwargs.get("queryset",
                                                Child._meta.get_field('clinic').remote_field.model.objects).all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentProfileForm
    list_display = ['id', 'first_name', 'last_name', 'phone_number',
                    'parent_email', 'date_added', 'is_active', 'user_created', 'children_count']
    search_fields = ['first_name', 'last_name', 'phone_number', 'parent_email']
    list_filter = ['is_active', 'date_added']
    readonly_fields = ['date_added', 'user']
    inlines = [ChildInline]

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'parent_email', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('user', 'date_added'),
            'classes': ('collapse',),
            'description': 'Auto-generated fields'
        })
    )

    def has_module_permission(self, request):
        """Allow Neuvii Admin full access, others limited"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Neuvii Admin', 'Clinic Admin', 'Therapist', 'Parent']
        return False

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        # Neuvii Admin can view all
        if request.user.role and request.user.role.name == 'Neuvii Admin':
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        if not self.has_module_permission(request):
            return False
        # Neuvii Admin and Clinic Admin can add clients
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            return request.user.role.name in ['Clinic Admin']
        return False

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        # Neuvii Admin has full permission
        if request.user.role and request.user.role.name == 'Neuvii Admin':
            return True
        # Others have limited permission
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Clinic Admin']
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        # Only Neuvii Admin can delete clients
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name == 'Neuvii Admin'
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user').prefetch_related('children')
        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        user_role = request.user.role.name
        if user_role == 'Neuvii Admin':
            return qs  # Full access for Neuvii Admin
        elif user_role == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                # Show clients whose children are in this clinic
                return qs.filter(children__clinic=request.user.clinic_admin).distinct()
            return qs.none()
        elif user_role == 'Therapist':
            if hasattr(request.user, 'therapist_profile'):
                # Show clients whose children are assigned to this therapist
                return qs.filter(children__assigned_therapist=request.user.therapist_profile).distinct()
            return qs.none()
        elif user_role == 'Parent':
            if hasattr(request.user, 'parent_profile'):
                return qs.filter(id=request.user.parent_profile.id)
            return qs.none()
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and obj.parent_email:
            messages.info(request,
                          f"Creating client profile for {obj.first_name} {obj.last_name}. "
                          f"User account and welcome email will be sent to {obj.parent_email}."
                          )

        super().save_model(request, obj, form, change)

        if obj.user:
            messages.success(request,
                             f"Client user account created successfully for {obj.parent_email}. "
                             f"Welcome email sent with login credentials."
                             )
        elif not change and obj.parent_email:
            messages.warning(request,
                             f"Client profile created but user account creation may have failed. "
                             f"Please check if {obj.parent_email} is already registered."
                             )

    def save_formset(self, request, form, formset, change):
        """Handle saving of child inline formset"""
        instances = formset.save(commit=False)
        for instance in instances:
            # Auto-assign clinic for clinic admin
            if request.user.role and request.user.role.name == 'Clinic Admin':
                if hasattr(request.user, 'clinic_admin'):
                    instance.clinic = request.user.clinic_admin
            instance.save()
        formset.save_m2m()

    def user_created(self, obj):
        return "Yes" if obj.user else "No"

    user_created.short_description = "User Account"

    def children_count(self, obj):
        return obj.children.count()

    children_count.short_description = "Children"


# Remove separate Child admin since children are managed through Parent inline
# But keep it for reference/advanced management for Neuvii Admin
@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    form = ChildForm
    list_display = ['id', 'name', 'age', 'gender', 'clinic', 'parent',
                    'assigned_therapist', 'created_at']
    search_fields = ['name', 'parent__first_name', 'parent__last_name',
                     'assigned_therapist__first_name', 'assigned_therapist__last_name']
    list_filter = ['clinic', 'gender', 'created_at', 'assigned_therapist']

    def has_module_permission(self, request):
        """Only show Child admin for Neuvii Admin for advanced management"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            # Only Neuvii Admin can see Child as separate admin
            return request.user.role.name == 'Neuvii Admin'
        return False

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        return True

    def has_add_permission(self, request):
        if not self.has_module_permission(request):
            return False
        return True

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        user_role = request.user.role.name
        if user_role == 'Neuvii Admin':
            return qs  # Full access for Neuvii Admin
        return qs.none()

    def save_model(self, request, obj, form, change):
        # Auto-assign clinic for clinic admin
        if request.user.role and request.user.role.name == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                obj.clinic = request.user.clinic_admin

        super().save_model(request, obj, form, change)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'child', 'therapist', 'task', 'due_date',
                    'completed', 'assigned_date']
    list_filter = ['therapist', 'completed', 'due_date', 'assigned_date']
    search_fields = ['child__name', 'therapist__first_name',
                     'therapist__last_name', 'task__title']
    date_hierarchy = 'assigned_date'

    def has_module_permission(self, request):
        """Allow access based on role"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Neuvii Admin', 'Clinic Admin', 'Therapist', 'Parent']
        return False

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        return True

    def has_add_permission(self, request):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            return request.user.role.name in ['Clinic Admin', 'Therapist']
        return False

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            if request.user.role.name == 'Parent':
                return obj and obj.child.parent.user == request.user
            return request.user.role.name in ['Clinic Admin', 'Therapist']
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name == 'Neuvii Admin'
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        user_role = request.user.role.name
        if user_role == 'Neuvii Admin':
            return qs  # Full access for Neuvii Admin
        elif user_role == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                return qs.filter(child__clinic=request.user.clinic_admin)
            return qs.none()
        elif user_role == 'Therapist':
            if hasattr(request.user, 'therapist_profile'):
                return qs.filter(therapist=request.user.therapist_profile)
            return qs.none()
        elif user_role == 'Parent':
            if hasattr(request.user, 'parent_profile'):
                return qs.filter(child__parent=request.user.parent_profile)
            return qs.none()
        return qs.none()


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['id', 'child', 'title', 'is_long_term']
    list_filter = ['is_long_term', 'child__clinic']
    search_fields = ['title', 'child__name']

    def has_module_permission(self, request):
        """Allow access based on role"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Neuvii Admin', 'Clinic Admin', 'Therapist', 'Parent']
        return False

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        return True

    def has_add_permission(self, request):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            return request.user.role.name in ['Clinic Admin', 'Therapist']
        return False

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            if request.user.role.name == 'Parent':
                return False  # Parents can't change goals
            return request.user.role.name in ['Clinic Admin', 'Therapist']
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name == 'Neuvii Admin'
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        user_role = request.user.role.name
        if user_role == 'Neuvii Admin':
            return qs  # Full access for Neuvii Admin
        elif user_role == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                return qs.filter(child__clinic=request.user.clinic_admin)
            return qs.none()
        elif user_role == 'Therapist':
            if hasattr(request.user, 'therapist_profile'):
                return qs.filter(child__assigned_therapist=request.user.therapist_profile)
            return qs.none()
        elif user_role == 'Parent':
            if hasattr(request.user, 'parent_profile'):
                return qs.filter(child__parent=request.user.parent_profile)
            return qs.none()
        return qs.none()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'goal', 'title', 'difficulty']
    list_filter = ['difficulty', 'goal__is_long_term']
    search_fields = ['title', 'goal__title', 'goal__child__name']

    def has_module_permission(self, request):
        """Allow access based on role, but not for Parents"""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name in ['Neuvii Admin', 'Clinic Admin', 'Therapist']
        return False

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        return True

    def has_add_permission(self, request):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            return request.user.role.name in ['Clinic Admin', 'Therapist']
        return False

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            if request.user.role.name == 'Neuvii Admin':
                return True  # Full permission for Neuvii Admin
            return request.user.role.name in ['Clinic Admin', 'Therapist']
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if hasattr(request.user, 'role') and request.user.role:
            return request.user.role.name == 'Neuvii Admin'
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated or not request.user.role:
            return qs.none()

        user_role = request.user.role.name
        if user_role == 'Neuvii Admin':
            return qs  # Full access for Neuvii Admin
        elif user_role == 'Clinic Admin':
            if hasattr(request.user, 'clinic_admin'):
                return qs.filter(goal__child__clinic=request.user.clinic_admin)
            return qs.none()
        elif user_role == 'Therapist':
            if hasattr(request.user, 'therapist_profile'):
                return qs.filter(goal__child__assigned_therapist=request.user.therapist_profile)
            return qs.none()
        return qs.none()