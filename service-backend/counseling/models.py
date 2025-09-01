# service-backend/counseling/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

User = settings.AUTH_USER_MODEL

class Consultant(models.Model):
    """
    Represents a consultant (Psychology or Business) registered on the platform.
    This links a User account to consultant-specific details.
    """
    SPECIALTY_CHOICES = [
        ('psychology', _('Psychology')),
        ('business', _('Business')),
        # Add more specialties if needed
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='consultant_profile',
        verbose_name=_("user")
    )
    specialty = models.CharField(
        _("specialty"), max_length=20, choices=SPECIALTY_CHOICES
    )
    bio = models.TextField(_("biography"), blank=True)
    # Hourly rate, if applicable for display or future payment features
    hourly_rate = models.DecimalField(
        _("hourly rate"), max_digits=10, decimal_places=2, blank=True, null=True
    )
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("Consultant")
        verbose_name_plural = _("Consultants")

    def __str__(self):
        specialty_display = self.get_specialty_display()
        return f"{self.user.get_full_name()} ({specialty_display})"


class ConsultantSchedule(models.Model):
    """
    Represents a time slot when a consultant is available for booking.
    """
    consultant = models.ForeignKey(
        Consultant,
        related_name='schedules',
        on_delete=models.CASCADE,
        verbose_name=_("consultant")
    )
    date = models.DateField(_("date"))
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))

    SLOT_STATUS_CHOICES = [
        ('available', _('Available')),
        ('booked', _('Booked')),
        ('cancelled', _('Cancelled')),
    ]
    slot_status = models.CharField(
        _("slot status"), max_length=20, choices=SLOT_STATUS_CHOICES, default='available'
    )

    class Meta:
        verbose_name = _("Consultant Schedule")
        verbose_name_plural = _("Consultant Schedules")
        ordering = ['date', 'start_time']
        # Ensure no overlapping schedules for the same consultant?
        # This might require custom validation.

    def __str__(self):
        return (f"{self.consultant} - {self.date} "
                f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} "
                f"({self.get_slot_status_display()})")

    @property
    def is_available(self):
        """Check if the slot is available for booking."""
        return self.slot_status == 'available'


class Appointment(models.Model):
    """
    Represents a booked appointment between a user and a consultant.
    """
    user = models.ForeignKey(
        User,
        related_name='appointments',
        on_delete=models.CASCADE,
        verbose_name=_("user")
    )
    consultant_schedule = models.OneToOneField(
        ConsultantSchedule,
        related_name='appointment',
        on_delete=models.CASCADE,
        verbose_name=_("consultant schedule")
    )
    # Store a snapshot of the schedule details at the time of booking
    # This is useful if the schedule details change later.
    booking_time = models.DateTimeField(_("booking time"), auto_now_add=True)
    
    APPOINTMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),       # Awaiting confirmation
        ('confirmed', _('Confirmed')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        # ('rescheduled', _('Rescheduled')), # If rescheduling is allowed
    ]
    status = models.CharField(
        _("status"), max_length=20, choices=APPOINTMENT_STATUS_CHOICES, default='pending'
    )
    # Optional: Add fields for appointment notes, meeting link, etc.
    # notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ['-booking_time']

    def __str__(self):
        return (f"Appointment: {self.user} with {self.consultant_schedule.consultant} "
                f"on {self.consultant_schedule.date} at {self.consultant_schedule.start_time}")

    def save(self, *args, **kwargs):
        # When an appointment is created/booked, update the related schedule's status
        if self.pk is None: # Only on creation
            self.consultant_schedule.slot_status = 'booked'
            self.consultant_schedule.save(update_fields=['slot_status'])
        super().save(*args, **kwargs)

    def cancel(self):
        """Cancel the appointment and free up the schedule slot."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])
        # Free up the schedule slot
        self.consultant_schedule.slot_status = 'available'
        self.consultant_schedule.save(update_fields=['slot_status'])

# Note: The prompt mentions sending SMS notifications upon booking.
# This will likely be handled in a Celery task, possibly defined in tasks.py.
