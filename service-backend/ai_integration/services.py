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

# --- Configuration ---
# These should ideally come from environment variables or Django settings
DEEPSEEK_API_URL = getattr(settings, 'DEEPSEEK_API_URL', None)
DEEPSEEK_API_KEY = getattr(settings, 'DEEPSEEK_API_KEY', None)

if not DEEPSEEK_API_URL:
    raise ImproperlyConfigured("DEEPSEEK_API_URL setting is not configured.")
# Note: API key might be in the header or body, depending on DeepSeek's API design.
# if not DEEPSEEK_API_KEY:
#     raise ImproperlyConfigured("DEEPSEEK_API_KEY setting is not configured.")


def send_to_deepseek_api(input_data: dict) -> dict:
    """
    Sends processed user data to the DeepSeek AI API and returns the response.

    Args:
        input_data (dict): The structured data (likely from `deepseek_input_json`)
                           ready to be sent to the AI.

    Returns:
        dict: The parsed JSON response from the DeepSeek API.
              Returns an empty dict or raises an exception on failure.

    Raises:
        requests.exceptions.RequestException: For network-related errors.
        ValueError: If the response cannot be parsed as JSON.
    """
    url = DEEPSEEK_API_URL
    headers = {
        'Content-Type': 'application/json',
        # 'Authorization': f'Bearer {DEEPSEEK_API_KEY}', # Example header, adjust as needed
    }
    # The payload/body sent to the AI
    # This structure depends heavily on how you design the prompt and what DeepSeek expects.
    # The `input_data` should already be formatted according to this design.
    payload = {
        # "model": "deepseek-chat", # Example model name, check DeepSeek docs
        "messages": [
            {
                "role": "system",
                # The system prompt is crucial for guiding the AI's behavior.
                # This is a placeholder, needs to be refined based on requirements.
                "content": (
                    "You are an expert talent identification AI. "
                    "Analyze the provided psychological assessment results. "
                    "Identify the user's key talents and provide clear, actionable recommendations "
                    "in areas like Academic, Career, and Artistic paths. "
                    "Respond in a structured JSON format."
                )
            },
            {
                "role": "user",
                "content": f"Analyze these results: {input_data}" # Or format input_data differently
            }
        ],
        # "stream": False, # Example parameter
    }

    try:
        logger.info(f"Sending data to DeepSeek API at {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=30) # Set a timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        # Attempt to parse JSON response
        ai_response_data = response.json()
        logger.info("Successfully received and parsed response from DeepSeek API.")
        return ai_response_data

    except requests.exceptions.Timeout:
        logger.error("Timeout occurred while sending data to DeepSeek API.")
        raise # Re-raise to be handled by the calling function/task
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred while sending data to DeepSeek API: {e}")
        raise # Re-raise
    except ValueError as e: # Includes json.JSONDecodeError
        logger.error(f"Error decoding JSON response from DeepSeek API: {e}")
        # Optionally, log the raw response content for debugging
        # logger.debug(f"Raw response content: {response.text}")
        raise # Re-raise

# --- Optional: Helper functions for processing AI response ---
# def parse_ai_recommendations(ai_output_data: dict, user_id: int) -> list:
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
