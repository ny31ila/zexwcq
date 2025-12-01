# service-backend/ai_integration/tasks.py
"""
Celery tasks for the ai_integration app.
This handles background processing for sending data to AI and processing its response.
"""
from celery import shared_task
import logging
from requests.exceptions import RequestException
from .services import call_external_ai_provider_and_save_results

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(RequestException,), # Only retry on network-related errors
    retry_kwargs={'max_retries': 3, 'countdown': 10} # Retry 3 times with a 10s delay
)
def send_to_ai(self, user_id: int, package_id: int, provider_key: str, model_key: str):
    """
    Celery task that acts as a lightweight wrapper to call the main AI service function.
    Handles automatic retries for transient network failures.
    """
    try:
        logger.info(
            f"Starting send_to_ai task for User ID: {user_id}, Package ID: {package_id}, "
            f"Provider: {provider_key}, Model: {model_key}"
        )

        interaction_id = call_external_ai_provider_and_save_results(
            user_id=user_id,
            package_id=package_id,
            provider_key=provider_key,
            model_key=model_key
        )

        success_message = f"Successfully processed AI interaction {interaction_id} for User {user_id}."
        logger.info(success_message)
        return success_message

    except RequestException as exc:
        # This exception will be caught by Celery to trigger a retry
        logger.warning(
            f"Network error in send_to_ai task for User {user_id}. Attempt {self.request.retries + 1} of {self.max_retries}. "
            f"Error: {exc}"
        )
        raise self.retry(exc=exc)

    except Exception as exc:
        # For non-network errors, log critically and do not retry.
        logger.critical(
            f"A non-recoverable error occurred in send_to_ai task for User {user_id}: {exc}",
            exc_info=True
        )
        # We don't re-raise here because these are considered final failures.
        return f"Failed: A non-recoverable error occurred: {exc}"


@shared_task
def test_celery_connection(message: str):
    """
    A simple test task to verify that the Celery-Redis connection is working.
    """
    logger.info(f"Celery test task received message: '{message}'")
    return f"Task executed successfully with message: '{message}'"
