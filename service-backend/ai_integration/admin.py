# service-backend/ai_integration/admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import AIRecommendation, AIProvider, AIInteraction
import json

@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'settings_config_key', 'is_active_for_users', 'created_at')
    list_filter = ('is_active_for_users',)
    search_fields = ('name', 'settings_config_key')
    ordering = ('name',)

@admin.register(AIInteraction)
class AIInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'provider', 'status', 'http_status_code', 'timestamp_sent')
    list_filter = ('status', 'provider', 'timestamp_sent')
    search_fields = ('user__national_code', 'user__first_name', 'user__last_name', 'package__id')
    readonly_fields = [
        'user', 'package', 'provider', 'status', 'pretty_full_request',
        'pretty_full_response', 'processed_response', 'http_status_code',
        'timestamp_sent', 'timestamp_received'
    ]

    fieldsets = (
        ('Overview', {
            'fields': ('user', 'package', 'provider', 'status', 'http_status_code')
        }),
        ('Timestamps', {
            'fields': ('timestamp_sent', 'timestamp_received')
        }),
        ('Request Payload', {
            'fields': ('pretty_full_request',)
        }),
        ('Response Payload', {
            'fields': ('pretty_full_response', 'processed_response')
        }),
    )

    def pretty_json_formatter(self, data):
        """Helper to format JSON data for display."""
        if data is None:
            return "(No data)"
        pretty_data = json.dumps(data, indent=4, ensure_ascii=False)
        # Use mark_safe to allow HTML rendering in the admin
        return mark_safe(f"<pre><code>{pretty_data}</code></pre>")

    @admin.display(description="Full Request")
    def pretty_full_request(self, obj):
        return self.pretty_json_formatter(obj.full_request)

    @admin.display(description="Full Response")
    def pretty_full_response(self, obj):
        return self.pretty_json_formatter(obj.full_response)

    # Ensure all fields are readonly by overriding has_add_permission and has_change_permission
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False # Set to True if you want admins to be able to "change" (view)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommendation_type', 'title', 'timestamp')
    list_filter = ('recommendation_type', 'timestamp')
    search_fields = (
        'user__national_code', 'user__first_name', 'user__last_name',
        'title', 'description'
    )
    readonly_fields = ('timestamp', 'updated_at') # These shouldn't be editable
    # raw_id_fields = ('user',) # Useful for large user sets
