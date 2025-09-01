# service-backend/counseling/views.py
from rest_framework import generics, status, permissions, filters, views
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
# Import your models and serializers
from .models import Consultant, ConsultantSchedule, Appointment
from .serializers import (
    ConsultantSerializer, ConsultantScheduleSerializer, AppointmentSerializer,
    BookAppointmentSerializer, CancelAppointmentSerializer
)
# Import user model
from django.conf import settings
User = settings.AUTH_USER_MODEL

class ConsultantListView(generics.ListAPIView):
    """
    List all active consultants.
    """
    queryset = Consultant.objects.filter(is_active=True)
    serializer_class = ConsultantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'bio']
    filterset_fields = ['specialty']
    ordering_fields = ['user__first_name', 'user__last_name']
    ordering = ['user__first_name', 'user__last_name']

class ConsultantDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific active consultant.
    """
    queryset = Consultant.objects.filter(is_active=True)
    serializer_class = ConsultantSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class ConsultantScheduleListView(generics.ListAPIView):
    """
    List available schedules for a specific consultant.
    """
    serializer_class = ConsultantScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date'] # Allow filtering schedules by date
    ordering = ['date', 'start_time']

    def get_queryset(self):
        consultant_id = self.kwargs.get('consultant_id')
        # Show only available slots for booking
        return ConsultantSchedule.objects.filter(
            consultant_id=consultant_id,
            slot_status='available'
        )

class UserAppointmentListView(generics.ListAPIView):
    """
    List all appointments for the authenticated user.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'consultant_schedule__consultant__specialty']
    ordering = ['-booking_time']

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

class ConsultantAppointmentListView(generics.ListAPIView):
    """
    List all appointments for the authenticated consultant.
    This view is intended for consultants to see their own bookings.
    The user making the request must have a Consultant profile.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-booking_time']

    def get_queryset(self):
        try:
            # Get the consultant profile for the requesting user
            consultant = self.request.user.consultant_profile
        except Consultant.DoesNotExist:
            # User is not a consultant
            return Appointment.objects.none() # Return empty queryset

        # Return appointments related to this consultant's schedules
        return Appointment.objects.filter(
            consultant_schedule__consultant=consultant
        )

class BookAppointmentView(views.APIView):
    """
    Book a new appointment for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BookAppointmentSerializer(data=request.data)
        if serializer.is_valid():
            schedule_id = serializer.validated_data['consultant_schedule_id']
            schedule = get_object_or_404(ConsultantSchedule, id=schedule_id)

            # Double-check availability (race condition)
            if not schedule.is_available:
                 return Response(
                     {"detail": _("Sorry, this slot is no longer available.")},
                     status=status.HTTP_409_CONFLICT # Conflict
                 )

            # Create the appointment
            appointment = Appointment.objects.create(
                user=request.user,
                consultant_schedule=schedule
                # status defaults to 'pending'
            )

            # Trigger SMS notification task (Celery)
            # from .tasks import send_appointment_sms
            # send_appointment_sms.delay(appointment.id)

            response_serializer = AppointmentSerializer(appointment, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CancelAppointmentView(views.APIView):
    """
    Cancel an existing appointment for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment, id=appointment_id, user=request.user
        )

        if appointment.status == 'cancelled':
            return Response(
                {"detail": _("This appointment is already cancelled.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform cancellation (updates status and schedule slot)
        appointment.cancel()

        # Trigger SMS notification task for cancellation (Celery)
        # from .tasks import send_cancellation_sms
        # send_cancellation_sms.delay(appointment.id)

        return Response(
            {"detail": _("Appointment cancelled successfully.")},
            status=status.HTTP_200_OK
        )

# If needed, a view for a consultant to confirm an appointment
# class ConfirmAppointmentView(views.APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, appointment_id, *args, **kwargs):
#         # Ensure the requesting user is the consultant for this appointment
#         appointment = get_object_or_404(
#             Appointment,
#             id=appointment_id,
#             consultant_schedule__consultant__user=request.user
#         )
#
#         if appointment.status != 'pending':
#             return Response(
#                 {"detail": _("This appointment cannot be confirmed.")},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         appointment.status = 'confirmed'
#         appointment.save(update_fields=['status'])
#
#         # Trigger confirmation SMS (Celery)
#         # from .tasks import send_confirmation_sms
#         # send_confirmation_sms.delay(appointment.id)
#
#         return Response(
#             {"detail": _("Appointment confirmed successfully.")},
#             status=status.HTTP_200_OK
#         )
