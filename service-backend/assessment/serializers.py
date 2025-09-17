# service-backend/assessment/serializers.py
from rest_framework import serializers
from django.conf import settings
from .models import TestPackage, Assessment, UserAssessmentAttempt

User = settings.AUTH_USER_MODEL # We'll use this for type hinting if needed

class TestPackageSerializer(serializers.ModelSerializer):
    """Serializer for TestPackage model."""
    # Include related assessments, showing just their names for brevity
    # Using StringRelatedField with many=True for the M2M relationship
    assessments = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = TestPackage
        fields = '__all__' # Or specify fields explicitly
        read_only_fields = ('created_at', 'updated_at', 'assessments') # assessments are read-only here

class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model."""
    # --- Updated to correctly reflect the M2M relationship ---
    # Show the names of the packages this assessment belongs to
    # Using StringRelatedField with many=True for the reverse M2M relationship via 'packages' related_name
    package_names = serializers.StringRelatedField(source='packages', many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = '__all__' # Or specify fields explicitly
        read_only_fields = ('created_at', 'updated_at', 'package_names') # package_names are read-only

class UserAssessmentAttemptSerializer(serializers.ModelSerializer):
    """Serializer for UserAssessmentAttempt model."""
    user_national_code = serializers.CharField(source='user.national_code', read_only=True)
    # --- Updated source for assessment name ---
    assessment_name = serializers.CharField(source='assessment.name', read_only=True)
    # --- Updated source for package names (accessing via the M2M relationship on Assessment) ---
    package_names = serializers.StringRelatedField(source='assessment.packages', many=True, read_only=True)
    duration = serializers.DurationField(read_only=True) # Calculated property

    class Meta:
        model = UserAssessmentAttempt
        fields = '__all__'
        read_only_fields = (
            'user', 'start_time', 'end_time', 'created_at', 'updated_at',
            'user_national_code', 'assessment_name', 'package_names', 'duration',
            # These fields should not be modified via standard API update
            'is_completed', 'raw_results_json', 'processed_results_json' # Add processed_results_json
        )

class UserAssessmentAttemptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a UserAssessmentAttempt."""
    class Meta:
        model = UserAssessmentAttempt
        fields = ('assessment',) # Only need assessment ID to start an attempt
        # assessment is required

    def validate_assessment(self, value):
        """Ensure the assessment is active."""
        if not value.is_active:
            raise serializers.ValidationError("This assessment is not currently available.")
        return value

# --- UPDATED SERIALIZER FOR INCREMENTAL RESPONSE SAVING ---
class SaveAssessmentResponseSerializer(serializers.Serializer):
    """
    Serializer for saving a user response incrementally.
    Expects the raw response data for one or more questions.
    The structure is: {"response_data": {"question_id_1": {...}, "question_id_2": {...}}}
    The key of the `response_data` dict is the `question_id`.
    The value is the response details (e.g., {"response": true, "time_spent_ms": 1200}).
    """
    # The structure of responses for one or more questions.
    # The key is the question_id, the value is the response details.
    response_data = serializers.DictField(
        child=serializers.DictField(), # Value is a dict of response details
        required=True,
        help_text=(
            "Dictionary where the key is the 'question_id' and the value is a dictionary "
            "containing the response details (e.g., {'response': true, 'time_spent_ms': 1200})."
        )
    )

    def validate_response_data(self, value):
        """Validate that response_data is a non-empty dictionary and keys are strings."""
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError(
                "response_data must be a non-empty JSON object."
            )
        # Further validation that keys are strings happens implicitly by DictField key type.
        # The actual content of each question's response value (dict) is validated by the view
        # logic or the service function based on the specific assessment/question schema.
        return value

# --- SERIALIZER FOR STARTING AN ATTEMPT ---
# This can be kept simple, potentially reusing or aliasing UserAssessmentAttemptCreateSerializer
# Or creating a specific one if start logic needs unique validation.
# For now, UserAssessmentAttemptCreateSerializer is sufficient for starting.

# --- SERIALIZER FOR SUBMITTING AN ATTEMPT ---
class UserAssessmentAttemptSubmitSerializer(serializers.ModelSerializer):
    """
    Serializer for submitting/finalizing an assessment attempt.
    Marks the attempt as completed. Does NOT handle incremental saves.
    """
    # No specific fields are required in the request body for final submission
    # other than the action itself (handled by the view).

    class Meta:
        model = UserAssessmentAttempt
        fields = () # No fields to update directly in this serializer for submission

    def validate(self, data):
        """Add custom validation if needed before final submission."""
        # Example: Ensure the attempt belongs to the requesting user
        # This check should ideally be done in the view logic based on the request user
        # and the attempt instance, not just the data being submitted.
        # request = self.context.get('request')
        # if request and self.instance and self.instance.user != request.user:
        #     raise serializers.ValidationError("You do not have permission to update this attempt.")

        # Example: Ensure the attempt is not already completed (redundant check, view also does this)
        if self.instance and self.instance.is_completed:
             raise serializers.ValidationError("This assessment attempt is already completed.")

        return data

    def update(self, instance, validated_data):
        """Custom update logic to finalize the attempt."""
        # --- Finalize the attempt ---
        instance.is_completed = True
        # Correct way to set end_time to now
        from django.utils import timezone
        instance.end_time = timezone.now()

        # --- Important: Do NOT modify raw_results_json here ---
        # raw_results_json is already populated incrementally by the save-response endpoint.
        # This serializer/view is only responsible for marking it complete.

        # --- Important: Do NOT populate processed_results_json here ---
        # processed_results_json should be populated by a background task (e.g., Celery)
        # that reads raw_results_json, performs calculations, and saves the result.
        # This keeps the submission endpoint fast and defers heavy processing.
        # instance.processed_results_json = process_raw_results_to_ai_format(instance.raw_results_json)
        # The line above is conceptual. The actual processing happens elsewhere.

        instance.save()
        # --- Trigger Celery task to process results and send to AI ---
        # This is conceptual. The actual task definition will be in assessment/tasks.py
        # and will be triggered here.
        # from .tasks import process_assessment_and_send_to_ai
        # process_assessment_and_send_to_ai.delay(instance.id)

        return instance
