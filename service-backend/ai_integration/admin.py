# service-backend/ai_integration/admin.py
from django.contrib import admin
from .models import AIRecommendation

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