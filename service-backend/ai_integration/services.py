# service-backend/ai_integration/services.py
"""
Service functions for preparing and logging AI requests.
"""
import logging
import json
from pathlib import Path
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

# Define the path for the log file within the ai_integration app directory
LOG_FILE_PATH = Path(__file__).parent / "ai_request_log.json"
User = get_user_model()

def generate_ai_request(aggregated_data: dict):
    """
    Generates a structured JSON AI request payload and logs it to a file.
    """
    user_data = aggregated_data.get("user_data", {})

    # Construct the structured JSON prompt
    prompt = {
        "system_instructions": {
            "role": "You are an expert career counselor providing guidance to Iranian users.",
            "language": "Generate the entire response in Persian (Farsi).",
            "response_guidelines": [
                "Begin your analysis with a brief, evaluative summary of the user's profile to build trust and rapport.",
                "Carefully examine the user's personal information (age, gender, etc.) and the results from all completed assessments.",
                "Synthesize findings to identify key strengths, personality traits, interests, and potential areas for development.",
                "Provide a comprehensive report that includes a summary of the user's profile, personalized career path suggestions, and recommendations for skill development.",
                "Your tone should be encouraging, professional, and easy to understand. Avoid jargon and focus on providing practical advice.",
                "IMPORTANT: This is a one-time, static report. Do NOT ask the user questions or suggest any form of further interaction or conversation."
            ],
            "output_format": {
                "format": "Structure your response in a clear and organized manner. Use headings and bullet points to improve readability.",
                "tables": "Use tables where appropriate to present data or comparisons clearly."
            }
        },
        "user_profile": {
            "age": user_data.get("age"),
            "gender": user_data.get("gender"),
            # Add any other important user metadata here
        },
        "assessment_results": aggregated_data.get("assessments_data", [])
    }

    # For now, we will just log the aggregated data to a file.
    # In the future, this function will be responsible for sending the request to the AI service.
    payload = {
        "prompt": prompt,
        "Temperature": 0,
        "hallucination": 0
    }

    try:
        # Use json.dumps with ensure_ascii=False to correctly handle Persian characters
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, indent=2, ensure_ascii=False))
            f.write("\n---\n") # Separator for multiple requests
        logger.info(f"Successfully logged AI request to {LOG_FILE_PATH}")
    except IOError as e:
        logger.error(f"Failed to write AI request to log file: {e}")
        # Depending on the desired behavior, you might want to re-raise the exception
        # or handle it gracefully. For now, we'll just log it.
