# service-backend/counseling/tasks.py
"""
Celery tasks for the counseling app.
Handles background processing for sending SMS notifications related to appointments.
"""

# Import Celery instance (Will be configured later)
# from celery import shared_task
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# import logging

# from .models import Appointment
# from util.services import send_sms # Import a generic SMS sending utility function

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
# def send_appointment_sms(self, appointment_id):
#     """
#     Celery task to send SMS notification to user and consultant upon booking.
#     """
#     try:
#         appointment = Appointment.objects.select_related(
#             'user', 'consultant_schedule__consultant__user'
#         ).get(id=appointment_id)
#     except Appointment.DoesNotExist:
#         logger.error(f"Appointment with id {appointment_id} does not exist for SMS notification.")
#         return f"Failed: Appointment {appointment_id} not found"

#     try:
#         user_phone = appointment.user.phone_number
#         consultant_phone = appointment.consultant_schedule.consultant.user.phone_number
#         consultant_name = appointment.consultant_schedule.consultant.user.get_full_name()
#         appointment_date = appointment.consultant_schedule.date
#         start_time = appointment.consultant_schedule.start_time
#         end_time = appointment.consultant_schedule.end_time

#         # --- Send SMS to User ---
#         user_message = (
#             f"رزرو نوبت مشاوره شما با موفقیت انجام شد.\n"
#             f"مشاور: {consultant_name}\n"
#             f"تاریخ: {appointment_date}\n"
#             f"ساعت: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
#             f"لطفاً در زمان مقرر حاضر شوید."
#         )
#         send_sms(user_phone, user_message) # Implement this function in util/services.py
#         logger.info(f"Sent booking confirmation SMS to user {appointment.user.national_code}.")

#         # --- Send SMS to Consultant ---
#         consultant_message = (
#             f"یک نوبت جدید برای مشاوره رزرو شده است.\n"
#             f"کاربر: {appointment.user.get_full_name()}\n"
#             f"تاریخ: {appointment_date}\n"
#             f"ساعت: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
#         )
#         send_sms(consultant_phone, consultant_message)
#         logger.info(f"Sent booking notification SMS to consultant {consultant_name}.")

#         return f"Success: SMS sent for Appointment {appointment_id}"

#     except Exception as exc:
#         logger.error(f"Failed to send SMS for Appointment {appointment_id}: {exc}", exc_info=True)
#         raise self.retry(exc=exc) # Re-raise to trigger retry

# @shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
# def send_cancellation_sms(self, appointment_id):
#     """
#     Celery task to send SMS notification upon appointment cancellation.
#     """
#     try:
#         appointment = Appointment.objects.select_related(
#             'user', 'consultant_schedule__consultant__user'
#         ).get(id=appointment_id)
#     except Appointment.DoesNotExist:
#         logger.error(f"Appointment with id {appointment_id} does not exist for cancellation SMS.")
#         return f"Failed: Appointment {appointment_id} not found"

#     try:
#         user_phone = appointment.user.phone_number
#         consultant_phone = appointment.consultant_schedule.consultant.user.phone_number
#         consultant_name = appointment.consultant_schedule.consultant.user.get_full_name()
#         appointment_date = appointment.consultant_schedule.date
#         start_time = appointment.consultant_schedule.start_time

#         # --- Send SMS to User ---
#         user_message = (
#             f"نوبت مشاوره شما با {consultant_name} در تاریخ {appointment_date} "
#             f"ساعت {start_time.strftime('%H:%M')} لغو شد."
#         )
#         send_sms(user_phone, user_message)
#         logger.info(f"Sent cancellation SMS to user {appointment.user.national_code}.")

#         # --- Send SMS to Consultant ---
#         consultant_message = (
#             f"نوبت مشاوره با کاربر {appointment.user.get_full_name()} در تاریخ {appointment_date} "
#             f"ساعت {start_time.strftime('%H:%M')} توسط کاربر لغو شد."
#         )
#         send_sms(consultant_phone, consultant_message)
#         logger.info(f"Sent cancellation SMS to consultant {consultant_name}.")

#         return f"Success: Cancellation SMS sent for Appointment {appointment_id}"

#     except Exception as exc:
#         logger.error(f"Failed to send cancellation SMS for Appointment {appointment_id}: {exc}", exc_info=True)
#         raise self.retry(exc=exc)

# # If you add a confirmation feature:
# # @shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
# # def send_confirmation_sms(self, appointment_id):
# #     """Send SMS when consultant confirms the appointment."""
# #     # Implementation similar to above tasks
# #     pass
