# project_root/service-backend/assessment/admin.py
from django.contrib import admin
from .models import TestPackage, Assessment, UserAssessmentAttempt

@admin.register(TestPackage)
class TestPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'min_age', 'max_age', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'min_age', 'max_age')
    search_fields = ('name', 'description')
    ordering = ['min_age', 'name']

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    # --- Updated to reflect the ManyToManyField 'packages' ---
    # list_display: Cannot directly display a M2M field. We can create a custom method.
    list_display = ('name', 'get_packages_list', 'json_filename', 'is_active')
    # list_filter: Cannot directly filter by a M2M field in list_filter. We can create a custom filter or use the related model's field.
    # For simplicity here, we remove the direct 'package' filter.
    list_filter = ('is_active', 'created_at', 'packages') # Filtering by the M2M field itself is allowed
    search_fields = ('name', 'description', 'json_filename')
    # ordering: Cannot order by a M2M field directly.
    ordering = ['name']

    def get_packages_list(self, obj):
        """Custom method to display packages in list_display."""
        return ", ".join([p.name for p in obj.packages.all()[:3]]) # Show first 3 package names
    get_packages_list.short_description = 'Packages' # Sets the column name in the admin

@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'is_completed', 'start_time', 'end_time')
    # --- Updated the filter reference ---
    # 'assessment__package' is no longer valid as 'package' is not a field on 'Assessment'.
    # We can filter by 'assessment__packages' (the M2M field) or related fields on the package.
    list_filter = ('is_completed', 'start_time', 'assessment__packages') # Filter by the M2M field
    search_fields = ('user__national_code', 'user__first_name', 'user__last_name', 'assessment__name')
    readonly_fields = ('start_time', 'created_at', 'updated_at') # These shouldn't be editable
    # raw_id_fields = ('user', 'assessment') # Useful for large user/assessment sets
