# service-backend/ai_integration/tasks.py
"""
Celery tasks for the ai_integration app.
This handles background processing for sending data to AI and processing its response.
"""

# Import Celery instance (Will be configured later)
# from celery import shared_task
# from django.core.exceptions import ObjectDoesNotExist
# from django.conf import settings
# import logging

# from .models import AIRecommendation
# from .services import send_to_deepseek_api
# from assessment.models import UserAssessmentAttempt # To get data for AI
# from django.contrib.auth import get_user_model
# User = get_user_model()

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
# def process_ai_response(self, user_id, ai_response_data):
#     """
#     Celery task to process the AI response data and save recommendations to the database.
#     This task is typically called by the assessment app's task after sending data to AI.
#     """
#     try:
#         user = User.objects.get(id=user_id)
#     except User.DoesNotExist:
#         logger.error(f"User with id {user_id} does not exist for saving AI recommendations.")
#         return f"Failed: User {user_id} not found"

#     try:
#         # Parse the AI response data and create recommendation objects
#         # This parsing logic needs to match the structure of `ai_response_data`
#         # Example (needs adaptation):
#         recommendations_data = ai_response_data.get('recommendations', [])
#         created_count = 0
#         for item in recommendations_data:
#             AIRecommendation.objects.create(
#                 user=user,
#                 recommendation_type=item.get('type', 'general').lower(),
#                 title=item.get('title', 'Untitled Recommendation'),
#                 description=item.get('description', ''),
#                 deepseek_output_json=item # Store the raw item data
#             )
#             created_count += 1

#         logger.info(f"Successfully saved {created_count} recommendations for User {user_id}.")
#         return f"Success: Saved {created_count} recommendations for User {user_id}"

#     except Exception as exc:
#         logger.error(f"Failed to process AI response for User {user_id}: {exc}", exc_info=True)
#         raise self.retry(exc=exc)


# @shared_task
# def trigger_ai_analysis_for_user(user_id):
#     """
#     Celery task to trigger the full AI analysis process for a user.
#     1. Aggregate user's completed assessment data.
#     2. Prepare data for AI.
#     3. Send data to AI (via service).
#     4. Process AI response (via another task).
#     This provides a single entry point for initiating the AI analysis.
#     """
#     try:
#         user = User.objects.get(id=user_id)
#     except User.DoesNotExist:
#         logger.error(f"User with id {user_id} does not exist for AI analysis trigger.")
#         return f"Failed: User {user_id} not found"

#     # 1. Aggregate completed assessment attempts
#     completed_attempts = UserAssessmentAttempt.objects.filter(user=user, is_completed=True)

#     if not completed_attempts.exists():
#         logger.info(f"No completed assessments found for User {user_id}. Skipping AI analysis.")
#         return f"Skipped: No completed assessments for User {user_id}"

#     # 2. Prepare data (this logic might be in a model method or service)
#     # Example: Collect all `deepseek_input_json` from attempts
#     aggregated_data = []
#     for attempt in completed_attempts:
#         if attempt.deepseek_input_json:
#             # Add metadata or structure as needed for the AI prompt
#             aggregated_data.append({
#                 'assessment_name': attempt.assessment.name,
#                 'data': attempt.deepseek_input_json
#             })
#         else:
#             logger.warning(f"Attempt {attempt.id} has no deepseek_input_json. Skipping.")

#     if not aggregated_data:
#         logger.info(f"No valid data found in completed assessments for User {user_id}.")
#         return f"Skipped: No valid data for User {user_id}"

#     # 3. Send to AI
#     try:
#         # The input structure for the AI service needs to be defined
#         # This is a placeholder structure
#         ai_input_payload = {
#             'user_id': user_id,
#             'assessments_data': aggregated_data
#             # Add other relevant user info if needed by the AI prompt
#         }
#         ai_response_data = send_to_deepseek_api(ai_input_payload)

#         # 4. Process response (call the other task)
#         # process_ai_response.delay(user_id, ai_response_data) # Call without .delay() if calling from another task
#         process_ai_response.delay(user_id, ai_response_data)

#         logger.info(f"AI analysis triggered and data sent for User {user_id}.")
#         return f"Success: AI analysis triggered for User {user_id}"

#     except Exception as exc:
#         logger.error(f"Failed to trigger AI analysis for User {user_id}: {exc}", exc_info=True)
#         # Depending on error type, might want to retry or just log
#         # For now, we'll log and not retry automatically from this task
#         return f"Failed: Error triggering AI analysis for User {user_id} - {exc}"
