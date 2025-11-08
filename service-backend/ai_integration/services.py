# service-backend/ai_integration/services.py
"""
Service functions for handling interactions with external AI providers.
"""
import logging
import json
import requests
from django.conf import settings
from .models import AIInteractionLog
from django.contrib.auth import get_user_model
from assessment.models import TestPackage

logger = logging.getLogger(__name__)
User = get_user_model()

def send_prompt_to_ollama_and_log(user_id: int, package_id: int, aggregated_data: dict):
    """
    Creates an AIInteractionLog, sends a prompt to the Ollama Cloud API,
    and updates the log with the response or error.
    """
    # 1. Get User and Package objects for creating the log
    try:
        user = User.objects.get(id=user_id)
        package = TestPackage.objects.get(id=package_id)
    except (User.DoesNotExist, TestPackage.DoesNotExist) as e:
        logger.error(f"Could not find User or Package for logging AI interaction: {e}")
        return

    # 2. Construct the prompt and payload
    user_data = aggregated_data.get("user_data", {})
    prompt = {
        "system_instructions": {
            "role": "You are an expert career counselor providing guidance to Iranian users.",
            "language": "Generate the entire response in Persian (Farsi).",
            "response_guidelines": [
                "Begin your analysis with a brief, evaluative summary of the user's profile to build trust and rapport.",
                "Synthesize findings to identify key strengths, personality traits, interests, and potential areas for development.",
                "Provide a comprehensive report that includes a summary of the user's profile, personalized career path suggestions, and recommendations for skill development.",
                "Your tone should be encouraging, professional, and easy to understand. Avoid jargon and focus on providing practical advice.",
                "IMPORTANT: This is a one-time, static report. Do NOT ask the user questions or suggest any form of further interaction or conversation."
            ],
            "output_format": {
                "format": "Use headings and bullet points for readability.",
                "tables": "Use tables where appropriate."
            }
        },
        "user_profile": {
            "age": user_data.get("age"),
            "gender": user_data.get("gender"),
        },
        "assessment_results": aggregated_data.get("assessments_data", [])
    }

    api_key = settings.OLLAMA_CLOUD_API_KEY
    model_id = settings.OLLAMA_CLOUD_MODEL_ID
    if not api_key or not model_id:
        logger.error("Ollama Cloud API key or model ID is not configured in settings.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # The prompt must be a string for the Ollama API
    prompt_string = json.dumps(prompt, ensure_ascii=False)

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt_string}],
        "stream": False,
        "options": {"temperature": 0.7}
    }

    # 3. Create the initial log record
    log_entry = AIInteractionLog.objects.create(
        user=user,
        package=package,
        status='pending',
        request_payload=payload
    )

    # 4. Make the API call and update the log
    try:
        url = "https://api.ollama.com/v1/chat/completions" # Corrected URL
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        response_content = data.get("message", {}).get("content", "")

        log_entry.status = 'success'
        log_entry.response_content = response_content
        log_entry.save()
        logger.info(f"Successfully received response from Ollama for user {user.id}")

    except requests.exceptions.RequestException as e:
        error_message = f"Request failed: {e}"
        log_entry.status = 'error'
        log_entry.error_message = error_message
        log_entry.save()
        logger.error(error_message)
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        log_entry.status = 'error'
        log_entry.error_message = error_message
        log_entry.save()
        logger.error(error_message, exc_info=True)
