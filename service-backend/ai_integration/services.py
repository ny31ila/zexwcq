# service-backend/ai_integration/services.py
"""
Service functions for preparing and logging AI requests.
"""
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the path for the log file within the ai_integration app directory
LOG_FILE_PATH = Path(__file__).parent / "ai_request_log.json"

def generate_ai_request(aggregated_data: dict):
    """
    Generates the AI request payload and logs it to a file.
    """
    prompt_template = """
    As an expert career counselor, your task is to analyze the provided assessment results
    and user information to generate personalized, insightful, and actionable career-related
    recommendations.

    **User and Assessment Data:**
    {user_and_assessment_data}

    **Instructions:**
    1.  **Review the Data:** Carefully examine the user's personal information (age, gender, education) and the results from all completed assessments.
    2.  **Synthesize Findings:** Identify key strengths, personality traits, interests, and potential areas for development based on a holistic view of the data.
    3.  **Generate Recommendations:** Provide a comprehensive report that includes:
        *   A summary of the user's profile.
        *   Personalized career path suggestions.
        *   Recommendations for skill development and further education.
        *   Actionable next steps for the user to take in their career exploration journey.
    4.  **Tone and Style:** Your response should be encouraging, professional, and easy to understand. Avoid jargon and focus on providing practical advice.

    **Output Format:**
    Please structure your response in a clear and organized manner. Use headings and bullet points to improve readability.
    """

    # For now, we will just log the aggregated data to a file.
    # In the future, this function will be responsible for sending the request to the AI service.
    
    payload = {
        "prompt": prompt_template.format(user_and_assessment_data=json.dumps(aggregated_data, indent=2)),
        "model": "some_future_model",
        "parameters": {
            "max_tokens": 2048,
            "temperature": 0.7,
        }
    }

    try:
        with open(LOG_FILE_PATH, "a") as f:
            f.write(json.dumps(payload, indent=2))
            f.write("\n---\n") # Separator for multiple requests
        logger.info(f"Successfully logged AI request to {LOG_FILE_PATH}")
    except IOError as e:
        logger.error(f"Failed to write AI request to log file: {e}")
        # Depending on the desired behavior, you might want to re-raise the exception
        # or handle it gracefully. For now, we'll just log it.
