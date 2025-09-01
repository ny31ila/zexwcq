# service-backend/resume/admin.py
from django.contrib import admin
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'template_type', 'created_at', 'updated_at')
    list_filter = ('template_type', 'created_at')
    search_fields = (
        'user__national_code', 'user__first_name', 'user__last_name',
        'title'
    )
    readonly_fields = ('created_at', 'updated_at', 'shareable_link_token')
    # raw_id_fields = ('user',) # Useful for large user sets
