# service-backend/assessment/serializers.py
from rest_framework import serializers
from django.conf import settings
from .models import TestPackage, Assessment, UserAssessmentAttempt

User = settings.AUTH_USER_MODEL # We'll use this for type hinting if needed

class TestPackageSerializer(serializers.ModelSerializer):
    """Serializer for TestPackage model."""
    # You might want to include a field to show related assessments
    # assessments = AssessmentSerializer(many=True, read_only=True)

    class Meta:
        model = TestPackage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model."""
    # Include package name for easier reference
    package_name = serializers.CharField(source='package.name', read_only=True)

    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class UserAssessmentAttemptSerializer(serializers.ModelSerializer):
    """Serializer for UserAssessmentAttempt model."""
    user_national_code = serializers.CharField(source='user.national_code', read_only=True)
    assessment_name = serializers.CharField(source='assessment.name', read_only=True)
    package_name = serializers.CharField(source='assessment.package.name', read_only=True)
    duration = serializers.DurationField(read_only=True) # Calculated property

    class Meta:
        model = UserAssessmentAttempt
        fields = '__all__'
        read_only_fields = (
            'user', 'start_time', 'end_time', 'created_at', 'updated_at',
            'user_national_code', 'assessment_name', 'package_name', 'duration'
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

# Serializer for submitting answers/results
class UserAssessmentAttemptSubmitSerializer(serializers.ModelSerializer):
    """Serializer for submitting results to a UserAssessmentAttempt."""
    # Expect raw_results_json to be provided in the request data
    # It's a JSONField, so DRF will handle parsing if content-type is application/json
    raw_results_json = serializers.JSONField(required=True)
    # deepseek_input_json might be processed on the backend, or also submitted
    # For now, let's assume it's processed, so we don't require it in submission

    class Meta:
        model = UserAssessmentAttempt
        fields = ('raw_results_json',) # Only update these fields

    def validate(self, data):
        """Add custom validation if needed."""
        # Example: Ensure the attempt belongs to the requesting user
        # This check should ideally be done in the view logic based on the request user
        # and the attempt instance, not just the data being submitted.
        # request = self.context.get('request')
        # if request and self.instance and self.instance.user != request.user:
        #     raise serializers.ValidationError("You do not have permission to update this attempt.")

        # Example: Ensure the attempt is not already completed
        if self.instance and self.instance.is_completed:
             raise serializers.ValidationError("This assessment attempt is already completed.")

        return data

    def update(self, instance, validated_data):
        """Custom update logic to finalize the attempt."""
        instance.raw_results_json = validated_data.get('raw_results_json', instance.raw_results_json)
        # Here you would typically process raw_results_json to create deepseek_input_json
        # instance.deepseek_input_json = process_results_for_ai(instance.raw_results_json)
        # For now, let's just copy it or leave it as None to be processed later/by Celery
        # instance.deepseek_input_json = instance.raw_results_json # Placeholder

        instance.is_completed = True
        instance.end_time = serializers.DateTimeField().to_representation(serializers.DateTimeField().to_internal_value(None)) # Set end time
        # Correct way to set end_time to now
        from django.utils import timezone
        instance.end_time = timezone.now()

        instance.save()
        # Trigger Celery task to send results to AI
        # from .tasks import send_results_to_ai
        # send_results_to_ai.delay(instance.id)
        return instance