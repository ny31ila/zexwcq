# service-backend/counseling/admin.py
from django.contrib import admin
from .models import Consultant, ConsultantSchedule, Appointment

@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'is_active')
    list_filter = ('specialty', 'is_active')
    search_fields = (
        'user__national_code', 'user__first_name', 'user__last_name'
    )
    # raw_id_fields = ('user',) # Useful for large user sets

@admin.register(ConsultantSchedule)
class ConsultantScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'consultant', 'date', 'start_time', 'end_time', 'slot_status'
    )
    list_filter = ('slot_status', 'date', 'consultant__specialty')
    search_fields = (
        'consultant__user__national_code',
        'consultant__user__first_name',
        'consultant__user__last_name'
    )
    date_hierarchy = 'date'
    # raw_id_fields = ('consultant',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'consultant_schedule', 'booking_time', 'status'
    )
    list_filter = ('status', 'booking_time', 'consultant_schedule__date')
    search_fields = (
        'user__national_code', 'user__first_name', 'user__last_name',
        'consultant_schedule__consultant__user__national_code',
        'consultant_schedule__consultant__user__first_name',
        'consultant_schedule__consultant__user__last_name'
    )
    date_hierarchy = 'booking_time'
    readonly_fields = ('booking_time',)
    # raw_id_fields = ('user', 'consultant_schedule')
