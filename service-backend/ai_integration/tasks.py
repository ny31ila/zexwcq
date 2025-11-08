# service-backend/ai_integration/tasks.py
"""
Celery tasks for the ai_integration app.
This handles background processing for sending data to AI and processing its response.
"""
from celery import shared_task
import logging

from assessment.services import prepare_aggregated_package_data_for_ai
from .services import send_prompt_to_ollama_and_log

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_to_ai(self, user_id, package_id):
    """
    Celery task to aggregate completed assessment results for a user within a specific package
    and send them to the AI integration service.
    """
    from django.contrib.auth import get_user_model
    from assessment.models import TestPackage
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        package = TestPackage.objects.get(id=package_id)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist for sending results to AI.")
        return f"Failed: User {user_id} not found"
    except TestPackage.DoesNotExist:
        logger.error(f"TestPackage with id {package_id} does not exist for sending results to AI.")
        return f"Failed: Package {package_id} not found"

    try:
        logger.info(f"Starting send_to_ai task for User {user_id}, Package {package_id}")

        aggregated_data = prepare_aggregated_package_data_for_ai(user, package)

        if not aggregated_data or not aggregated_data.get("assessments_data"):
            warning_msg = f"No completed assessment data found for User {user_id}, Package {package_id}. Nothing to send to AI."
            logger.warning(warning_msg)
            return f"Skipped: {warning_msg}"

        send_prompt_to_ollama_and_log(user_id, package_id, aggregated_data)

        logger.info(f"Successfully initiated sending data to AI for User {user_id}, Package {package_id}.")
        return f"Success: Data sent to AI for User {user_id}, Package {package_id}"

    except Exception as exc:
        logger.error(
            f"Failed to send data to AI for User {user_id}, Package {package_id}: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc)
