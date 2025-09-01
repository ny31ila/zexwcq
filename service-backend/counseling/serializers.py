# service-backend/counseling/serializers.py
from rest_framework import serializers
from .models import Consultant, ConsultantSchedule, Appointment

class ConsultantSerializer(serializers.ModelSerializer):
    """Serializer for Consultant model."""
    user_full_name = serializers.CharField(
        source='user.get_full_name', read_only=True
    )
    user_national_code = serializers.CharField(
        source='user.national_code', read_only=True
    )

    class Meta:
        model = Consultant
        fields = '__all__'
        read_only_fields = ('user', 'user_full_name', 'user_national_code')


class ConsultantScheduleSerializer(serializers.ModelSerializer):
    """Serializer for ConsultantSchedule model."""
    consultant_name = serializers.CharField(
        source='consultant.user.get_full_name', read_only=True
    )
    consultant_specialty = serializers.CharField(
        source='consultant.get_specialty_display', read_only=True
    )

    class Meta:
        model = ConsultantSchedule
        fields = '__all__'
        read_only_fields = (
            'consultant', 'consultant_name', 'consultant_specialty'
        )


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model."""
    user_national_code = serializers.CharField(
        source='user.national_code', read_only=True
    )
    consultant_name = serializers.CharField(
        source='consultant_schedule.consultant.user.get_full_name', read_only=True
    )
    consultant_specialty = serializers.CharField(
        source='consultant_schedule.consultant.get_specialty_display', read_only=True
    )
    appointment_date = serializers.DateField(
        source='consultant_schedule.date', read_only=True
    )
    appointment_start_time = serializers.TimeField(
        source='consultant_schedule.start_time', read_only=True
    )
    appointment_end_time = serializers.TimeField(
        source='consultant_schedule.end_time', read_only=True
    )

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = (
            'user', 'consultant_schedule', 'booking_time',
            'user_national_code', 'consultant_name', 'consultant_specialty',
            'appointment_date', 'appointment_start_time', 'appointment_end_time'
        )

# Serializer for booking an appointment
class BookAppointmentSerializer(serializers.Serializer):
    """Serializer for booking a new appointment."""
    consultant_schedule_id = serializers.IntegerField()

    def validate_consultant_schedule_id(self, value):
        """Check if the schedule slot exists and is available."""
        try:
            schedule = ConsultantSchedule.objects.get(id=value)
        except ConsultantSchedule.DoesNotExist:
            raise serializers.ValidationError(
                _("The specified schedule slot does not exist.")
            )
        if not schedule.is_available:
            raise serializers.ValidationError(
                _("The selected schedule slot is not available.")
            )
        return value

# Serializer for cancelling an appointment
class CancelAppointmentSerializer(serializers.Serializer):
    """Serializer for cancelling an appointment."""
    # This serializer might not need fields, just the instance context.
    # Confirmation logic can be handled in the view.
    pass # Or add a confirmation field like `confirm = serializers.BooleanField()`
