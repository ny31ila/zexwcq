# service-backend/assessment/urls.py
from django.urls import path
from . import views

app_name = 'assessment'

urlpatterns = [
    # Test Packages
    path('packages/', views.TestPackageListView.as_view(), name='package_list'),
    path('packages/<int:id>/', views.TestPackageDetailView.as_view(), name='package_detail'),

    # Assessments (within accessible packages)
    path('assessments/', views.AssessmentListView.as_view(), name='assessment_list'),
    path('assessments/<int:id>/', views.AssessmentDetailView.as_view(), name='assessment_detail'),

    # User Assessment Attempts
    path('attempts/', views.UserAssessmentAttemptListView.as_view(), name='attempt_list'),
    path('attempts/start/', views.StartAssessmentAttemptView.as_view(), name='attempt_start'),
    path('attempts/<int:id>/submit/', views.SubmitAssessmentAttemptView.as_view(), name='attempt_submit'),

    # Optional: Endpoint to get assessment JSON data
    # path('assessments/<int:assessment_id>/data/', views.AssessmentJSONDataView.as_view(), name='assessment_json_data'),
]