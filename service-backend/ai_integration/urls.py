# service-backend/ai_integration/urls.py
from django.urls import path
from . import views

app_name = 'ai_integration'

urlpatterns = [
    path('recommendations/', views.UserAIRecommendationListView.as_view(), name='recommendation_list'),
    path('recommendations/<int:id>/', views.UserAIRecommendationDetailView.as_view(), name='recommendation_detail'),
    # path('trigger-analysis/', views.TriggerAIAnalysisView.as_view(), name='trigger_analysis'), # Optional
    # path('analysis-status/<str:task_id>/', views.AIAnalysisStatusView.as_view(), name='analysis_status'), # Optional
]
