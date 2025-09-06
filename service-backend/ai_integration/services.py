# service-backend/ai_integration/services.py
"""
Service functions for interacting with the external DeepSeek AI API.
This module handles the HTTP requests and responses.
"""

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

# --- OpenRouter Configuration for Testing ---
# New settings for the test task
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = getattr(settings, 'OPENROUTER_API_KEY', None)
# Default test model - can be changed later
OPENROUTER_TEST_MODEL = getattr(settings, 'OPENROUTER_TEST_MODEL')
# Optional headers for OpenRouter ranking
OPENROUTER_SITE_URL = getattr(settings, 'OPENROUTER_SITE_URL', 'http://localhost:8000') # Default for local dev
OPENROUTER_SITE_NAME = getattr(settings, 'OPENROUTER_SITE_NAME', 'NexaTalentDiscovery')

# --- New Service Function for Testing with OpenRouter ---
def send_test_prompt_to_openrouter(prompt_text: str) -> dict:
    """
    Sends a test prompt to the OpenRouter API using a free model.
    This is used to test the Celery/Redis setup.

    Args:
        prompt_text (str): The text prompt to send to the AI.

    Returns:
        dict: The parsed JSON response from the OpenRouter API.
              Returns an empty dict or raises an exception on failure.

    Raises:
        ImproperlyConfigured: If the OpenRouter API key is not configured.
        requests.exceptions.RequestException: For network-related errors.
        ValueError: If the response cannot be parsed as JSON.
    """
    if not OPENROUTER_API_KEY:
        raise ImproperlyConfigured("OPENROUTER_API_KEY setting is not configured for testing.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL, # Optional, for OpenRouter rankings
        "X-Title": OPENROUTER_SITE_NAME,    # Optional, for OpenRouter rankings
    }
    
    payload = {
        "model": OPENROUTER_TEST_MODEL,
        "messages": [
            {
                "role": "user",
                "content": 'tell me whats 2+2 in python.'
            }
        ],
        # Add other parameters if needed by the model/OpenRouter
        # "max_tokens": 1000, # Example
        # "temperature": 0.7, # Example
    }

    try:
        logger.info(f"Sending test prompt to OpenRouter API at {OPENROUTER_API_URL}")
        logger.debug(f"Prompt: {prompt_text}")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60) # Longer timeout for testing
        logger.debug(f"OpenRouter API response status: {response.status_code}")
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        # Attempt to parse JSON response
        ai_response_data = response.json()
        logger.info("Successfully received and parsed response from OpenRouter API (Test).")
        logger.debug(f"OpenRouter API response data: {ai_response_data}")
        return ai_response_data

    except requests.exceptions.Timeout:
        logger.error("Timeout occurred while sending data to OpenRouter API (Test).")
        raise # Re-raise to be handled by the calling function/task
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred while sending data to OpenRouter API (Test): {e}")
        logger.debug(f"Response content (if any): {getattr(e.response, 'text', 'N/A')}")
        raise # Re-raise
    except ValueError as e: # Includes json.JSONDecodeError
        logger.error(f"Error decoding JSON response from OpenRouter API (Test): {e}")
        # Log the raw response content for debugging
        logger.debug(f"Raw response content: {getattr(response, 'text', 'N/A')}")
        raise # Re-raise

# --- Optional: Helper functions for processing AI response ---
# def parse_ai_recommendations(ai_output_data, user_id: int) -> list:
#     """
#     Parses the raw AI output and creates AIRecommendation model instances.
#     This function needs to be aligned with the actual structure of `ai_output_data`.
#     """
#     recommendations = []
#     # Example parsing logic (needs to be adapted):
#     # Assume ai_output_data has a key 'recommendations' which is a list of dicts
#     raw_recommendations = ai_output_data.get('recommendations', [])
#     for item in raw_recommendations:
#         rec = AIRecommendation(
#             user_id=user_id,
#             recommendation_type=item.get('type', 'general').lower(),
#             title=item.get('title', 'Untitled Recommendation'),
#             description=item.get('description', ''),
#             deepseek_output_json=item # Store the specific item as raw data
#         )
#         recommendations.append(rec)
#     return recommendations
