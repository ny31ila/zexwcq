# service-backend/career/serializers.py
from rest_framework import serializers
from .models import JobOpening, BusinessResource

class JobOpeningSerializer(serializers.ModelSerializer):
    """Serializer for JobOpening model."""
    posted_by_name = serializers.SerializerMethodField() # Readable name of the poster

    class Meta:
        model = JobOpening
        fields = '__all__'
        read_only_fields = ('posted_at', 'posted_by', 'posted_by_name')

    def get_posted_by_name(self, obj):
        if obj.posted_by:
            return f"{obj.posted_by.first_name} {obj.posted_by.last_name}".strip() or obj.posted_by.national_code
        return None

class BusinessResourceSerializer(serializers.ModelSerializer):
    """Serializer for BusinessResource model."""
    added_by_name = serializers.SerializerMethodField() # Readable name of the contributor

    class Meta:
        model = BusinessResource
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'added_by', 'added_by_name')

    def get_added_by_name(self, obj):
        if obj.added_by:
            return f"{obj.added_by.first_name} {obj.added_by.last_name}".strip() or obj.added_by.national_code
        return None

# If a feature for users to ask business consultants is added later,
# a serializer for that request model would go here.
# Example:
# class AskBusinessConsultantSerializer(serializers.Serializer):
#     subject = serializers.CharField(max_length=255)
#     message = serializers.CharField()
#     # The user would be taken from the request context
