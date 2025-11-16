# service-backend/ai_integration/views.py
from rest_framework import views, response, permissions, status
from django.conf import settings
from .models import AIProvider

class AvailableAIModelsView(views.APIView):
    """
    Provides a list of currently active AI providers and their available models.
    This endpoint is for the frontend to populate selection UIs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Returns a structured list of active providers and their models.
        """
        active_providers = AIProvider.objects.filter(is_active_for_users=True)
        provider_settings = settings.AI_PROVIDERS

        available_models_data = []

        for provider in active_providers:
            config_key = provider.settings_config_key
            if config_key in provider_settings:
                provider_config = provider_settings[config_key]
                models = provider_config.get('MODELS', {})

                if models:
                    available_models_data.append({
                        'provider_name': provider.name,
                        'provider_key': config_key,
                        'models': [
                            {
                                'model_key': model_key,
                                'display_name': model_details.get('display_name', model_key)
                            }
                            for model_key, model_details in models.items()
                        ]
                    })

        return response.Response({
            "status": "success",
            "data": available_models_data
        }, status=status.HTTP_200_OK)
