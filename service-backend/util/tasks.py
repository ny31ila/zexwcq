# service-backend/util/tasks.py
"""
General Celery tasks for the project that don't belong to a specific app.
This includes common utilities like sending SMS.
"""

# Import Celery instance (Will be configured later)
# from celery import shared_task
# import logging
# # Import SMS gateway library or service (e.g., Kavenegar, Ghasedak, etc.)
# # For example, if using a generic requests-based service:
# # import requests
# # from django.conf import settings

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
# def send_sms(self, phone_number, message):
#     """
#     General Celery task to send an SMS.
#     This task encapsulates the logic for interacting with the SMS service provider.
#     It can be called by other app tasks (e.g., counseling, account).
#     """
#     try:
#         # --- SMS Sending Logic ---
#         # This part needs to be implemented based on your chosen SMS provider's API.
#         # Example using a hypothetical API:
#         #
#         # sms_api_url = settings.SMS_API_URL
#         # api_key = settings.SMS_API_KEY
#         #
#         # payload = {
#         #     'receptor': phone_number,
#         #     'message': message,
#         #     'sender': settings.SMS_DEFAULT_SENDER # Optional
#         # }
#         # headers = {
#         #     'Authorization': f'Bearer {api_key}',
#         #     'Content-Type': 'application/json'
#         # }
#         #
#         # response = requests.post(sms_api_url, json=payload, headers=headers, timeout=10)
#         # response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
#         #
#         # logger.info(f"SMS sent successfully to {phone_number}.")
#         # return f"Success: SMS sent to {phone_number}"

#         # --- Placeholder Implementation ---
#         # Replace the above logic with your actual SMS provider's API call.
#         logger.info(f"Sending SMS to {phone_number}: {message}")
#         # Simulate sending (remove this in production)
#         # In a real scenario, you would integrate with an SMS service provider here.
#         print(f"[SIMULATED SMS] To: {phone_number}, Message: {message}")
#         return f"Simulated: SMS sent to {phone_number}"

#     except Exception as exc:
#         logger.error(f"Failed to send SMS to {phone_number}: {exc}", exc_info=True)
#         raise self.retry(exc=exc) # Re-raise to trigger retry

# # If you need other general utility tasks (e.g., sending emails, data processing):
# # @shared_task
# # def send_email_task(subject, message, recipient_list):
# #     # Implementation for sending emails
# #     pass
