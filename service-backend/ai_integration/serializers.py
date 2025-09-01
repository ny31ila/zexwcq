# service-backend/ai_integration/serializers.py
from rest_framework import serializers
from .models import AIRecommendation

class AIRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for AIRecommendation model."""
    user_national_code = serializers.CharField(source='user.national_code', read_only=True)

    class Meta:
        model = AIRecommendation
        fields = '__all__'
        read_only_fields = (
            'user', 'timestamp', 'updated_at', 'user_national_code'
        ) # These fields should not be modified via API

# If there are specific endpoints for triggering AI processing or checking status,
# serializers for those requests/responses can be added here.
# For example:
# class TriggerAIProcessingSerializer(serializers.Serializer):
#     # Might just require user ID from context, or specific assessment attempt IDs
#     pass

# class AIProcessingStatusSerializer(serializers.Serializer):
#     status = serializers.CharField() # e.g., 'pending', 'processing', 'completed', 'failed'
#     message = serializers.CharField(required=False)