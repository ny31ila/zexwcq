# service-backend/career/admin.py
from django.contrib import admin
from .models import JobOpening, BusinessResource

@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_by', 'is_active', 'posted_at')
    list_filter = ('is_active', 'posted_at', 'location')
    search_fields = ('title', 'company', 'description', 'requirements')
    readonly_fields = ('posted_at',)
    # raw_id_fields = ('posted_by',) # Useful for large user sets

@admin.register(BusinessResource)
class BusinessResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'added_by', 'is_active', 'created_at')
    list_filter = ('resource_type', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    # raw_id_fields = ('added_by',) # Useful for large user sets
