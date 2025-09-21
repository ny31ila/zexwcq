# service-backend/assessment/views.py
from rest_framework import generics, status, permissions, filters, views
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
# Import your models and serializers
from .models import TestPackage, Assessment, UserAssessmentAttempt
from .serializers import (
    TestPackageSerializer, AssessmentSerializer,
    UserAssessmentAttemptSerializer, UserAssessmentAttemptCreateSerializer,
    UserAssessmentAttemptSubmitSerializer, SaveAssessmentResponseSerializer
)
# Import the new service function
from .services import calculate_assessment_scores, prepare_aggregated_package_data_for_ai
# Import the Celery task
from .tasks import send_to_ai
# Import user model
from django.conf import settings
User = settings.AUTH_USER_MODEL

# --- Views for Test Packages ---

class TestPackageListView(generics.ListAPIView):
    """
    List all active test packages, filtered by the authenticated user's age.
    """
    serializer_class = TestPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'min_age', 'max_age', 'price']
    ordering = ['min_age', 'name']

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age() # Assuming this method exists on the User model

        if user_age is not None:
            # Filter packages based on user's age
            queryset = TestPackage.objects.filter(is_active=True, min_age__lte=user_age, max_age__gte=user_age)
        else:
            # If age is not available, maybe show all or none? Let's show none for security/safety.
            # Or, you could show packages with min_age=0 or a default range.
            # For now, let's be restrictive.
            queryset = TestPackage.objects.none() # Or TestPackage.objects.filter(is_active=True, min_age=0)

        return queryset

class TestPackageDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific test package (if user has access based on age).
    """
    serializer_class = TestPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id' # Use 'id' to look up the package

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age()

        if user_age is not None:
            # Allow access only if package is active and age-appropriate
            return TestPackage.objects.filter(is_active=True, min_age__lte=user_age, max_age__gte=user_age)
        else:
            return TestPackage.objects.none()

# --- Views for Assessments ---

class AssessmentListView(generics.ListAPIView):
    """
    List assessments within packages accessible to the authenticated user (based on age).
    """
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    # Allow filtering by packages (IDs) that contain the assessments the user can access
    # --- Updated filter reference to use 'packages' (the M2M field) ---
    filterset_fields = ['packages'] # Filter by package ID (M2M field on Assessment)

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age()

        if user_age is not None:
             # Get IDs of packages accessible to the user based on age
             accessible_package_ids = TestPackage.objects.filter(
                 is_active=True, min_age__lte=user_age, max_age__gte=user_age
             ).values_list('id', flat=True)

             # Get assessments that belong to any of these accessible packages
             # Use distinct() to avoid duplicates if an assessment is in multiple accessible packages
             return Assessment.objects.filter(
                 is_active=True, packages__in=accessible_package_ids # Updated filter using M2M
             ).distinct()
        else:
            return Assessment.objects.none()

class AssessmentDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific assessment (if user has access to its package).
    """
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age()

        if user_age is not None:
            # Get IDs of packages accessible to the user based on age
            accessible_package_ids = TestPackage.objects.filter(
                is_active=True, min_age__lte=user_age, max_age__gte=user_age
            ).values_list('id', flat=True)

            # Get assessments that belong to any of these accessible packages
            return Assessment.objects.filter(
                is_active=True, packages__in=accessible_package_ids # Updated filter using M2M
            ).distinct() # Use distinct to prevent duplicates
        else:
            return Assessment.objects.none()

# --- Views for User Assessment Attempts (Nested under Assessment) ---

# --- NEW VIEW: Detail view for a specific user's attempt on a specific assessment ---
class UserAssessmentAttemptDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of the authenticated user's specific attempt for a given assessment.
    This view is nested under /assessments/<assessment_id>/attempt/.
    """
    serializer_class = UserAssessmentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id' # This will be the attempt's ID, but we find it via assessment_id and user

    def get_object(self):
        """
        Override get_object to find the attempt based on assessment_id from URL and user.
        """
        user = self.request.user
        # The assessment_id comes from the URL kwargs
        assessment_id = self.kwargs.get('assessment_id')

        # Find the attempt for this user and assessment
        # get_object_or_404 handles the case where the attempt doesn't exist
        attempt = get_object_or_404(
            UserAssessmentAttempt,
            user=user,
            assessment_id=assessment_id
            # No need for is_completed=False filter here, user can view any attempt
        )
        return attempt


# --- UPDATED VIEW: Start a new attempt for a specific assessment ---
class StartAssessmentAttemptView(views.APIView):
    """
    Start a new attempt for a specific assessment.
    This view is nested under /assessments/<assessment_id>/attempt/start/.
    Enforces that a user can only have one active (incomplete) attempt per assessment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, assessment_id, *args, **kwargs):
        """
        POST request to start an attempt.
        `assessment_id` is passed in the URL.
        """
        user = request.user

        # 1. Get the assessment instance based on the ID from the URL
        assessment = get_object_or_404(Assessment, id=assessment_id, is_active=True)

        # 2. --- Enforced Check: One Active Attempt Per User/Assessment ---
        existing_attempt = UserAssessmentAttempt.objects.filter(
            user=user, assessment=assessment, is_completed=False
        ).first()
        if existing_attempt:
            return Response(
                {
                    "detail": "You have an existing incomplete attempt for this assessment.",
                    "attempt_id": existing_attempt.id
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Check if user has access to the package this assessment belongs to based on age.
        user_age = user.calculate_age()
        # Get packages this specific assessment belongs to
        assessment_packages = assessment.packages.filter(is_active=True)

        # Check if any of the assessment's packages are accessible to the user
        accessible_package = assessment_packages.filter(
            min_age__lte=user_age, max_age__gte=user_age
        ).first() if user_age is not None else None

        if not accessible_package:
             return Response(
                 {"detail": "You do not have access to this assessment based on your age or package."},
                 status=status.HTTP_403_FORBIDDEN
             )

        # 4. Create the new attempt
        attempt = UserAssessmentAttempt.objects.create(
            user=user,
            assessment=assessment,
            start_time=timezone.now()
        )
        response_serializer = UserAssessmentAttemptSerializer(attempt)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# --- UPDATED VIEW: Submit/finalize an assessment attempt ---
class SubmitAssessmentAttemptView(views.APIView):
    """
    Submit results for an assessment attempt, marking it as completed.
    This view is nested under /assessments/<assessment_id>/attempt/submit/.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, assessment_id, *args, **kwargs):
        """
        PATCH request to submit/finalize an attempt.
        `assessment_id` is passed in the URL.
        """
        user = request.user

        # 1. Find the *incomplete* attempt for this user and assessment
        attempt = get_object_or_404(
            UserAssessmentAttempt,
            user=user,
            assessment_id=assessment_id,
            is_completed=False # Must be incomplete to submit
        )

        # 2. Validate using the serializer (basic validation)
        serializer = UserAssessmentAttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Raises 400 if invalid

        # 3. --- Finalize the attempt ---
        attempt.is_completed = True
        attempt.end_time = timezone.now()
        attempt.save(update_fields=['is_completed', 'end_time', 'updated_at'])

        # 4. --- NEW: Trigger immediate score calculation service ---
        # After the attempt is marked as completed, calculate the scores.
        calculation_result = calculate_assessment_scores(attempt.id)
        # Optionally, log the result or handle errors from the service
        # For example, if calculation failed, you might want to return a different status
        # or trigger a retry mechanism. For now, we assume success or internal handling.
        if calculation_result['status'] == 'error':
             # Log the error, perhaps return a warning in the response
             # logger.error(calculation_result['message']) # Assuming logger is imported
             pass # Or handle as needed

        # 5. Prepare and return the updated attempt data
        response_serializer = UserAssessmentAttemptSerializer(attempt)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# --- UPDATED VIEW: Incrementally Save User Responses ---
class SaveAssessmentResponseView(views.APIView):
    """
    Incrementally save a user's response to a single question within an attempt.
    This view is nested under /assessments/<assessment_id>/attempt/save-response/.
    The `question_id` is expected as the key in the `response_data` JSON object.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, assessment_id, *args, **kwargs):
        """
        PATCH request to save/update a single response.
        `assessment_id` is passed in the URL.
        Request body contains `response_data` for one question.
        Expected structure: {"question_id_key": {"response": ..., "time_spent_ms": ...}}
        """
        user = request.user

        # 1. Get the *incomplete* attempt instance for this user and assessment from the URL
        # Ensure the attempt exists, belongs to the user, and is for the specified assessment, and is incomplete.
        attempt = get_object_or_404(
            UserAssessmentAttempt,
            user=user,
            assessment_id=assessment_id,
            is_completed=False # Must be incomplete to save responses
        )

        # 2. Validate the incoming request data
        serializer = SaveAssessmentResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.validated_data['response_data']

        # 3. --- Core Logic: Update raw_results_json incrementally ---
        # Get the current raw_results_json (could be None or {})
        current_raw_results = attempt.raw_results_json or {}

        # --- Key Change: Assume response_data is a dictionary where the key IS the question_id ---
        # And the value is the response details (e.g., {"response": true, "time_spent_ms": 1200})
        # Example expected request body:
        # {
        #   "response_data": {
        #     "HOLLAND_INT_Q1": { "response": true, "time_spent_ms": 1200 },
        #     "MBTI_Q2": { "response": "A", "confidence": 0.8 }
        #   }
        # }
        # The key of the outer response_data dict is the question_id.

        if not isinstance(response_data, dict) or not response_data:
            return Response(
                {"detail": "response_data must be a non-empty JSON object where the key is the question_id."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Iterate through the provided response_data (should ideally be one question, but handle multiple)
        # The key is the question_id, the value is the response details.
        for question_id, response_details in response_data.items():
            if not question_id:
                continue # Skip if somehow question_id is falsy

            # If the question_id already exists and its value is a dictionary, merge the new response_details
            if question_id in current_raw_results and isinstance(current_raw_results[question_id], dict):
                current_raw_results[question_id].update(response_details)
            else:
                # Otherwise, just set it (this handles both new questions and cases where the existing value is not a dict)
                current_raw_results[question_id] = response_details

        # 4. Save the updated JSON back to the model instance
        attempt.raw_results_json = current_raw_results
        # Update the updated_at timestamp
        attempt.save(update_fields=['raw_results_json', 'updated_at'])

        # 5. Return success response, listing the question IDs that were saved
        saved_question_ids = list(response_data.keys())
        return Response(
            {
                "detail": "Response(s) saved successfully.",
                "saved_question_ids": saved_question_ids
            },
            status=status.HTTP_200_OK
        )


# --- Views for Overall User Assessment Attempts (Not nested) ---

class UserAssessmentAttemptListView(generics.ListAPIView):
    """
    List all assessment attempts for the authenticated user.
    This is a general list view, not specific to one assessment.
    """
    serializer_class = UserAssessmentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['start_time', 'end_time', 'assessment__name']
    ordering = ['-start_time']
    # --- Updated filter reference to use 'assessment__packages' (the M2M field) ---
    filterset_fields = ['assessment__packages', 'assessment', 'is_completed'] # Filter by package, assessment, status

    def get_queryset(self):
        return UserAssessmentAttempt.objects.filter(user=self.request.user)


# --- NEW VIEW: Manually Trigger Sending Package Results to AI ---
class SendPackageResultsToAiView(views.APIView):
    """
    Manually trigger the process of sending completed assessment results
    for a specific package to the AI service.

    This endpoint should be called by the user/frontend *after* ensuring
    all required assessments in the package are completed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, package_id, *args, **kwargs):
        """
        POST request to send results for a specific package to the AI.
        `package_id` is passed in the URL.
        """
        user = request.user

        # 1. Get the package instance and verify user access
        try:
            package = TestPackage.objects.get(id=package_id, is_active=True)
        except TestPackage.DoesNotExist:
            return Response(
                {"detail": "Test package not found or is inactive."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify the user has access to this package based on age
        user_age = user.calculate_age()
        if not (user_age is not None and package.min_age <= user_age <= package.max_age):
             return Response(
                 {"detail": "You do not have access to this package based on your age."},
                 status=status.HTTP_403_FORBIDDEN
             )

        # 2. Get all assessments belonging to the specified package
        package_assessments = package.assessments.filter(is_active=True)
        package_assessment_ids = list(package_assessments.values_list('id', flat=True))

        if not package_assessment_ids:
            return Response(
                {"detail": "This package contains no active assessments."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Get all completed UserAssessmentAttempts for the user and those specific assessments
        completed_attempts = UserAssessmentAttempt.objects.filter(
            user=user,
            assessment_id__in=package_assessment_ids,
            is_completed=True
        )

        completed_assessment_ids = list(completed_attempts.values_list('assessment_id', flat=True))

        # 4. --- Validation: Check if ALL required assessments are completed ---
        # Find assessments in the package that do not have a completed attempt by the user
        missing_assessment_ids = set(package_assessment_ids) - set(completed_assessment_ids)

        if missing_assessment_ids:
            missing_assessments = Assessment.objects.filter(id__in=missing_assessment_ids)
            missing_names = ", ".join([a.name for a in missing_assessments])
            return Response(
                {
                    "detail": f"Cannot send to AI. Missing completed attempts for assessments: {missing_names}",
                    "missing_assessments": missing_names.split(", ") # Optional: structured list
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. --- Trigger the Celery Task ---
        # All validations passed. Trigger the background task to send data to AI.
        # The task will handle the aggregation and AI service call.
        task_result = send_to_ai.delay(user.id, package.id)

        return Response(
            {
                "detail": "Request to send results to AI has been initiated.",
                "package_id": package.id,
                "package_name": package.name,
                "task_id": task_result.id # Optional: Provide task ID for status checking
            },
            status=status.HTTP_202_ACCEPTED
        )
