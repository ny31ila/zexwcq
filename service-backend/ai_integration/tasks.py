# service-backend/ai_integration/tasks.py
"""
Celery tasks for the ai_integration app.
This handles background processing for sending data to AI and processing its response.
"""

# Import Celery instance (Will be configured later)
from celery import shared_task
from django.core.exceptions import ImproperlyConfigured
import logging

# Import the new service function
from .services import send_test_prompt_to_openrouter

logger = logging.getLogger(__name__)

# ... (existing tasks like process_ai_response, trigger_ai_analysis_for_user - keep as is) ...


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def test_openrouter_task(self, prompt_text: str):
    """
    Celery task to send a test prompt to the OpenRouter API.
    This task is used to verify the Celery/Redis setup.
    """
    try:
        logger.info(f"Starting test_openrouter_task with prompt: {prompt_text}")
        # Call the service function to interact with the OpenRouter API
        # The service function will handle configuration errors (like missing API key)
        ai_response_data = send_test_prompt_to_openrouter(prompt_text)

        # Extract the model's response content
        # The structure depends on the OpenAI/OpenRouter chat completion format
        try:
            response_content = ai_response_data["choices"][0]["message"]["content"]
            logger.info(f"OpenRouter Test Task Successful. Response: {response_content}")
            return {
                "status": "success",
                "prompt": prompt_text,
                "response": response_content,
                "raw_response": ai_response_data # Include raw data for debugging
            }
        except (KeyError, IndexError) as e:
            error_msg = f"Error parsing OpenRouter response structure: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw response data: {ai_response_data}")
            # Return error status but still complete the task
            return {
                "status": "error",
                "prompt": prompt_text,
                "error": error_msg,
                "raw_response": ai_response_data
            }

    # Remove the explicit ImproperlyConfigured check here.
    # The service function or the request itself will raise exceptions if config is bad.
    # except ImproperlyConfigured as e:
    #     error_msg = f"Configuration error in test_openrouter_task: {e}"
    #     logger.error(error_msg)
    #     # Don't retry for configuration errors
    #     return {
    #         "status": "error",
    #         "prompt": prompt_text,
    #         "error": error_msg
    #     }
    except Exception as exc:
        logger.error(f"Failed to execute test_openrouter_task: {exc}", exc_info=True)
        # Re-raise the exception to trigger retry based on autoretry_for
        raise self.retry(exc=exc)


# ... (other existing tasks) ...
