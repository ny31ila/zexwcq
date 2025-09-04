# service-backend/assessment/admin.py
from django.contrib import admin
from .models import TestPackage, Assessment, UserAssessmentAttempt

@admin.register(TestPackage)
class TestPackageAdmin(admin.ModelAdmin):
    # --- Updated to manage assessments from the Package admin ---
    list_display = ('name', 'price', 'min_age', 'max_age', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'min_age', 'max_age')
    search_fields = ('name', 'description')
    ordering = ['min_age', 'name']
    # Add the assessments field to the form
    filter_horizontal = ('assessments',) # This provides a nice widget for M2M fields

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    # --- Simplified as the relationship is managed from TestPackage admin ---
    list_display = ('name', 'json_filename', 'is_active')
    # list_filter: Removed package filter as it's managed from the other side
    # If you still want to filter assessments by whether they belong to *any* package:
    # You might need a custom filter or filter by 'packages__isnull'
    list_filter = ('is_active', 'created_at') # , ('packages', admin.BooleanFieldListFilter) # Example custom filter idea
    search_fields = ('name', 'description', 'json_filename')
    ordering = ['name']
    # No need for custom methods related to packages here anymore

@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'is_completed', 'start_time', 'end_time')
    # --- Updated the filter reference ---
    # Filter by the related M2M field on the Assessment model
    list_filter = ('is_completed', 'start_time', 'assessment__packages')
    search_fields = ('user__national_code', 'user__first_name', 'user__last_name', 'assessment__name')
    readonly_fields = ('start_time', 'created_at', 'updated_at')
    # raw_id_fields = ('user', 'assessment')
