# service-backend/util/services.py
"""
General utility service functions that don't belong to a specific app model.
These are synchronous functions that can be called by views, tasks, or other services.
"""

import logging
# from django.core.mail import send_mail # If sending emails is needed
# from django.conf import settings

logger = logging.getLogger(__name__)

# Example: A synchronous wrapper or helper for sending SMS
# This function would typically be called by the Celery task in util/tasks.py
# or directly in views if synchronous sending is acceptable (not recommended for user-facing requests).
def send_sms_sync(phone_number, message):
    """
    Synchronous function to send an SMS.
    This is a placeholder and should be replaced with actual integration logic.
    For user-facing requests, prefer using the Celery task `util.tasks.send_sms`.
    """
    # --- SMS Sending Logic (Synchronous) ---
    # Similar to the logic in `util.tasks.send_sms`, but runs in the main thread.
    # This is generally not recommended for API views due to potential delays.
    #
    # Example using a hypothetical API:
    # import requests
    # sms_api_url = settings.SMS_API_URL
    # api_key = settings.SMS_API_KEY
    #
    # payload = {
    #     'receptor': phone_number,
    #     'message': message,
    # }
    # headers = {'Authorization': f'Bearer {api_key}'}
    #
    # try:
    #     response = requests.post(sms_api_url, data=payload, headers=headers, timeout=10)
    #     response.raise_for_status()
    #     logger.info(f"SMS sent synchronously to {phone_number}.")
    #     return True
    # except requests.exceptions.RequestException as e:
    #     logger.error(f"Error sending SMS to {phone_number}: {e}")
    #     return False

    # --- Placeholder Implementation ---
    logger.warning("Synchronous SMS sending is a placeholder. Use Celery task for production.")
    print(f"[SYNC SIMULATED SMS] To: {phone_number}, Message: {message}")
    return True # Indicate success/failure


# Example: A utility function for date conversions (if needed frequently)
# import jdatetime
# from datetime import datetime

# def convert_gregorian_to_shamsi(gregorian_date):
#     """Convert a Gregorian date to Shamsi (Jalali) string."""
#     if gregorian_date:
#         shamsi_date = jdatetime.date.fromgregorian(date=gregorian_date)
#         return shamsi_date.strftime('%Y/%m/%d')
#     return None

# Example: A utility function for generating shareable links
# import uuid
# def generate_shareable_link_token():
#     """Generate a unique token for shareable links."""
#     return uuid.uuid4()

# If you have other common utility functions (e.g., file processing, data validation):
# def validate_uploaded_file(file):
#     """Validate an uploaded file (e.g., type, size)."""
#     # Implementation
#     pass
