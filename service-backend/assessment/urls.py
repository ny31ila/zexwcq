# service-backend/assessment/urls.py
from django.urls import path
from . import views

app_name = 'assessment'

urlpatterns = [
    # Test Packages
    path('packages/', views.TestPackageListView.as_view(), name='package_list'),
    path('packages/<int:id>/', views.TestPackageDetailView.as_view(), name='package_detail'),
    # --- NEW URL: Endpoint to manually trigger sending package results to AI ---
    path('packages/<int:package_id>/send-to-ai/', views.SendPackageResultsToAiView.as_view(), name='send_package_to_ai'),

    # Assessments (within accessible packages)
    path('assessments/', views.AssessmentListView.as_view(), name='assessment_list'),
    path('assessments/<int:id>/', views.AssessmentDetailView.as_view(), name='assessment_detail'),

    # --- NEW NESTED URL STRUCTURE FOR USER ASSESSMENT ATTEMPTS ---
    # These URLs are now nested under a specific assessment ID.
    # This implies the attempt is for the authenticated user and the specified assessment.

    # User Assessment Attempt Detail (GET)
    path('assessments/<int:assessment_id>/attempt/', views.UserAssessmentAttemptDetailView.as_view(), name='attempt_detail'),
    
    # Start a new attempt for this assessment (POST)
    path('assessments/<int:assessment_id>/attempt/start/', views.StartAssessmentAttemptView.as_view(), name='attempt_start'),
    
    # Submit/finalize the attempt for this assessment (POST)
    path('assessments/<int:assessment_id>/attempt/submit/', views.SubmitAssessmentAttemptView.as_view(), name='attempt_submit'),
    
    # Save a single response for this assessment's attempt (PATCH)
    path('assessments/<int:assessment_id>/attempt/save-response/', views.SaveAssessmentResponseView.as_view(), name='save_response'),
    # --- END OF NESTED URL STRUCTURE ---

    # User's overall list of attempts (across all assessments)
    path('attempts/', views.UserAssessmentAttemptListView.as_view(), name='user_attempt_list'), # Renamed for clarity

    # Optional: Endpoint to get assessment JSON data
    # path('assessments/<int:assessment_id>/data/', views.AssessmentJSONDataView.as_view(), name='assessment_json_data'),
]
