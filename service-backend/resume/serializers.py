# service-backend/resume/serializers.py
from rest_framework import serializers
from .models import Resume

class ResumeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating a resume."""
    # data_json is required for creation/update
    # It's expected to be sent as a JSON object in the request body

    class Meta:
        model = Resume
        fields = ('title', 'template_type', 'data_json')
        # user is taken from the request context
        # generated_pdf, shareable_link_token, created_at, updated_at are read-only

    def create(self, validated_data):
        # Get the user from the request context
        user = self.context['request'].user
        resume = Resume.objects.create(user=user, **validated_data)
        return resume

class ResumeDetailSerializer(serializers.ModelSerializer):
    """Serializer for viewing resume details, including the shareable link."""
    user_national_code = serializers.CharField(source='user.national_code', read_only=True)
    shareable_link = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = '__all__'
        read_only_fields = (
            'user', 'user_national_code', 'generated_pdf',
            'shareable_link_token', 'shareable_link',
            'created_at', 'updated_at'
        )

    def get_shareable_link(self, obj):
        # This assumes the request is available in the context
        # to build the absolute URI. If not, you might need to pass the base URL.
        request = self.context.get('request')
        if request:
            # Use reverse if you have a named URL pattern
            # from django.urls import reverse
            # relative_url = reverse('resume:resume_share', kwargs={'token': obj.shareable_link_token})
            # return request.build_absolute_uri(relative_url)

            # Or construct manually (less robust)
            return request.build_absolute_uri(f'/api/resumes/share/{obj.shareable_link_token}/')
        return None # Or a relative path

class ResumeListSerializer(serializers.ModelSerializer):
    """Serializer for listing resumes (simpler view)."""
    user_national_code = serializers.CharField(source='user.national_code', read_only=True)

    class Meta:
        model = Resume
        fields = ('id', 'title', 'template_type', 'user_national_code', 'created_at', 'updated_at')
        read_only_fields = fields

# Serializer for triggering PDF generation
class GeneratePDFSerializer(serializers.Serializer):
    """Serializer for the request to generate a PDF."""
    # This serializer might not need any fields if it's just a trigger.
    # But you could add options here if needed (e.g., paper size, language).
    pass

# Serializer for the response after PDF generation request
class GeneratePDFResponseSerializer(serializers.Serializer):
    """Serializer for the response after requesting PDF generation."""
    detail = serializers.CharField()
    task_id = serializers.CharField(required=False) # If using Celery and returning task ID
