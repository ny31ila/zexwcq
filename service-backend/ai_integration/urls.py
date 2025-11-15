# service-backend/ai_integration/urls.py
from django.urls import path
from .views import AvailableAIModelsView

app_name = 'ai_integration'

urlpatterns = [
    path('available-models/', AvailableAIModelsView.as_view(), name='available-ai-models'),
]
