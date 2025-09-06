# service-backend/assessment/admin.py
from django.contrib import admin
from .models import TestPackage, Assessment, UserAssessmentAttempt

@admin.register(TestPackage)
class TestPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'min_age', 'max_age', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'min_age', 'max_age')
    search_fields = ('name', 'description')
    ordering = ['min_age', 'name']
    # --- Key Change: Use filter_horizontal for the M2M field ---
    # This provides a user-friendly widget to select Assessments for this Package.
    # This correctly implements the logic: "Edit Package -> Select Assessments"
    filter_horizontal = ('assessments',) # 'assessments' is the M2M field on TestPackage

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    # --- Simplified list_display for Assessment ---
    list_display = ('name', 'json_filename', 'is_active')
    # Removed 'packages' from list_filter as it's managed from TestPackage admin
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'json_filename')
    ordering = ['name']
    # Removed get_packages_list method from here as the relationship is managed from TestPackage

@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'is_completed', 'start_time', 'end_time')
    # --- Updated the filter reference to use 'assessment__packages' (the M2M field) ---
    list_filter = ('is_completed', 'start_time', 'assessment__packages') # Filter by packages
    search_fields = ('user__national_code', 'user__first_name', 'user__last_name', 'assessment__name')
    readonly_fields = ('start_time', 'created_at', 'updated_at') # These shouldn't be editable
