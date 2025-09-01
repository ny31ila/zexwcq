# service-backend/assessment/admin.py
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
    list_display = ('name', 'package', 'json_filename', 'is_active')
    list_filter = ('package', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'json_filename')
    ordering = ['package', 'name']

@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'is_completed', 'start_time', 'end_time')
    list_filter = ('is_completed', 'start_time', 'assessment__package')
    search_fields = ('user__national_code', 'user__first_name', 'user__last_name', 'assessment__name')
    readonly_fields = ('start_time', 'created_at', 'updated_at') # These shouldn't be editable
    # raw_id_fields = ('user', 'assessment') # Useful for large user/assessment sets