# service-backend/assessment/services.py
"""
Service functions for the assessment app.
This module contains the core business logic for processing assessment data,
such as calculating scores immediately after a user submits an attempt.
"""

# Import necessary modules
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import logging
import json

# Import models
from .models import UserAssessmentAttempt, Assessment

# Get logger for this module
logger = logging.getLogger(__name__)

# --- Service Function: Calculate Scores for a Single Attempt ---
def calculate_assessment_scores(attempt_id):
    """
    Service function to calculate scores for a completed UserAssessmentAttempt.
    This function reads the raw_results_json, performs calculations based on
    the associated Assessment's logic (potentially using its JSON file),
    and populates the processed_results_json field.

    This function is intended to be called immediately after an attempt is
    marked as completed (is_completed=True).

    Args:
        attempt_id (int): The ID of the UserAssessmentAttempt to process.

    Returns:
        dict: A dictionary containing the status and a message.
              Example: {'status': 'success', 'message': 'Scores calculated.'}
              Example: {'status': 'error', 'message': 'Error details...'}

    Raises:
        ObjectDoesNotExist: If the attempt_id is invalid.
    """
    try:
        # 1. Fetch the attempt instance from the database
        attempt = UserAssessmentAttempt.objects.select_related('assessment', 'user').get(id=attempt_id)
    except UserAssessmentAttempt.DoesNotExist:
        error_msg = f"UserAssessmentAttempt with id {attempt_id} does not exist for score calculation."
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}

    # 2. Validate preconditions for calculation
    if not attempt.is_completed:
        warning_msg = f"Attempt {attempt_id} is not completed. Skipping score calculation."
        logger.warning(warning_msg)
        return {'status': 'skipped', 'message': warning_msg}

    if not attempt.raw_results_json:
        warning_msg = f"Attempt {attempt_id} has no raw results data for score calculation."
        logger.warning(warning_msg)
        return {'status': 'skipped', 'message': warning_msg}

    # Get the associated assessment model instance
    assessment = attempt.assessment

    # 3. --- Core Logic: Perform Calculations ---
    # This is where the specific scoring logic for each assessment type would go.
    # The logic could be:
    # a) Hardcoded here based on assessment.name (e.g., if name=="MBTI": calculate_mbti(...))
    # b) Defined in separate functions within this file (e.g., calculate_holland_scores(...))
    # c) Defined in the Assessment model itself as a method (e.g., assessment.calculate_scores(...))
    # d) Read from the assessment's JSON file to get scoring rules (most flexible)

    # --- Placeholder/Example Logic ---
    # For demonstration, let's assume a simple scoring logic based on assessment name.
    # In reality, this would be much more complex and specific to each test.

    calculated_results = {}
    try:
        if assessment.name.lower() == "mbti":
            calculated_results = _calculate_mbti_scores(attempt.raw_results_json)
        elif assessment.name.lower() == "holland":
             calculated_results = _calculate_holland_scores(attempt.raw_results_json)
        elif assessment.name.lower() == "gardner":
             calculated_results = _calculate_gardner_scores(attempt.raw_results_json)
        # elif assessment.name.lower() == "swanson":
        #     calculated_results = _calculate_adhd_scores(attempt.raw_results_json)
        # elif assessment.name.lower() == "neo":
        #     calculated_results = _calculate_neo_scores(attempt.raw_results_json)
        # elif assessment.name.lower() == "disc":
        #     calculated_results = _calculate_disc_scores(attempt.raw_results_json)
        # elif assessment.name.lower() == "pvq":
        #     calculated_results = _calculate_pvq_scores(attempt.raw_results_json)
        # elif assessment.name.lower() == "schwartz values":
        #     calculated_results = _calculate_schwartz_scores(attempt.raw_results_json)
        else:
            # Generic handler or log unsupported assessment
            logger.info(f"No specific calculator implemented for assessment '{assessment.name}'. Using generic processor.")
            # Example generic processor: just count responses
            total_questions_answered = len(attempt.raw_results_json.keys()) if isinstance(attempt.raw_results_json, dict) else 0
            calculated_results = {
                "generic_summary": {
                    "assessment_name": assessment.name,
                    "total_questions_answered": total_questions_answered,
                    "processed_at": timezone.now().isoformat()
                }
            }

        # 4. --- Save Calculated Results ---
        # Update the attempt's processed_results_json field with the calculated data
        attempt.processed_results_json = calculated_results
        # Save only the processed_results_json field and updated_at
        attempt.save(update_fields=['processed_results_json', 'updated_at'])

        success_msg = f"Score calculation completed and saved for Attempt {attempt_id} ({assessment.name})."
        logger.info(success_msg)
        return {'status': 'success', 'message': success_msg}

    except Exception as e:
        error_msg = f"Failed to calculate scores for Attempt {attempt_id} ({assessment.name}): {e}"
        logger.exception(error_msg) # Logs the full traceback
        # Depending on requirements, you might want to save an error state in processed_results_json
        # or rely on the calling view/task to handle retries/errors.
        return {'status': 'error', 'message': error_msg}


# --- Helper Functions for Specific Assessments (Placeholders) ---

def _calculate_mbti_scores(raw_data):
    """Placeholder function to calculate MBTI scores."""
    # This would contain the actual logic to parse raw_data and compute MBTI dimensions.
    # Example (highly simplified):
    # counts = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
    # for q_id, response in raw_data.items():
    #     # Logic to map response to dimension increments
    #     # ...
    # # Calculate percentages
    # total_ei = counts['E'] + counts['I']
    # ei_percentage = {'E': (counts['E'] / total_ei) * 100 if total_ei > 0 else 0,
    #                  'I': (counts['I'] / total_ei) * 100 if total_ei > 0 else 0}
    # ... similarly for SN, TF, JP ...
    # return {
    #     "EI": ei_percentage,
    #     "SN": sn_percentage,
    #     "TF": tf_percentage,
    #     "JP": jp_percentage,
    #     "Personality_Type": determine_type(ei_percentage, sn_percentage, tf_percentage, jp_percentage)
    # }
    logger.debug("Calculating MBTI scores (placeholder logic)")
    return {
        "assessment_type": "MBTI",
        "placeholder_result": "Introversion: 60%, Intuition: 55%, Thinking: 70%, Judging: 65%",
        "details": "Actual MBTI calculation logic goes here."
    }

def _calculate_holland_scores(raw_data):
    """Placeholder function to calculate Holland (RIASEC) scores."""
    # This would parse the raw_data specific to the Holland test structure
    # (sections like interests, experiences, occupations, self-assessments)
    # and calculate scores for Realistic, Investigative, Artistic, Social, Enterprising, Conventional.
    logger.debug("Calculating Holland scores (placeholder logic)")
    return {
        "assessment_type": "Holland (RIASEC)",
        "placeholder_result": {
            "Realistic": 75,
            "Investigative": 60,
            "Artistic": 40,
            "Social": 55,
            "Enterprising": 50,
            "Conventional": 30
        },
        "details": "Actual Holland calculation logic goes here, processing sections and dimensions."
    }

def _calculate_gardner_scores(raw_data):
    """Placeholder function to calculate Gardner's Multiple Intelligences scores."""
    logger.debug("Calculating Gardner scores (placeholder logic)")
    return {
        "assessment_type": "Gardner's Multiple Intelligences",
        "placeholder_result": {
            "Linguistic": 80,
            "Logical-Mathematical": 70,
            "Spatial": 65,
            "Bodily-Kinesthetic": 55,
            "Musical": 45,
            "Interpersonal": 75,
            "Intrapersonal": 85,
            "Naturalistic": 60,
            "Existential": 50 # If applicable
        },
        "details": "Actual Gardner calculation logic goes here."
    }

# --- Future Expansion Point ---
# def _calculate_adhd_scores(raw_data):
#     """Logic for Swanson ADHD assessment."""
#     pass

# def _calculate_neo_scores(raw_data):
#     """Logic for NEO Personality Inventory."""
#     pass

# def _calculate_disc_scores(raw_data):
#     """Logic for DISC assessment."""
#     pass

# def _calculate_pvq_scores(raw_data):
#     """Logic for Portrait Values Questionnaire."""
#     pass

# def _calculate_schwartz_scores(raw_data):
#     """Logic for Schwartz Values Survey."""
#     pass


# --- Service Function: Aggregate Package Results for AI (Called by Task/View) ---
def prepare_aggregated_package_data_for_ai(user, package):
    """
    Service function to aggregate processed results from all completed assessments
    within a specific package for a user. This prepares the data structure
    that will be sent to the AI service.

    Args:
        user (User): The Django User instance.
        package (TestPackage): The TestPackage instance.

    Returns:
        dict: A dictionary containing the aggregated data structure ready for the AI,
              or None if preparation fails critically.
    """
    try:
        logger.info(f"Starting aggregation of package data for AI. User: {user.id}, Package: {package.id}")

        # 1. Get all assessments belonging to the specified package
        package_assessments = package.assessments.all()
        package_assessment_ids = list(package_assessments.values_list('id', flat=True))

        if not package_assessment_ids:
            logger.warning(f"Package {package.id} contains no assessments for AI data preparation.")
            return None # Or return an empty dict if that's preferred

        # 2. Get all completed UserAssessmentAttempts for the user and those specific assessments
        completed_attempts = UserAssessmentAttempt.objects.filter(
            user=user,
            assessment_id__in=package_assessment_ids,
            is_completed=True
        ).select_related('assessment')

        # 3. Prepare the data structure to send to the AI service.
        # The structure depends heavily on how the AI service expects the input.
        aggregated_ai_input_data = {
            "user_id": user.id,
            "package_id": package.id,
            "package_name": package.name,
            # "user_info": { # Optional: Include relevant user profile info if needed by AI prompt
            #     "national_code": user.national_code,
            #     "first_name": user.first_name,
            #     "last_name": user.last_name,
            #     # "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            #     # Add other relevant fields if needed by the AI prompt
            # },
            "assessments_data": []
        }

        # 4. Iterate through completed attempts and aggregate their processed results
        for attempt in completed_attempts:
            assessment_data = {
                "assessment_id": attempt.assessment.id,
                "assessment_name": attempt.assessment.name,
                # Include the processed results JSON from the attempt
                # This is the data calculated by calculate_assessment_scores
                "results": attempt.processed_results_json or {}
            }
            aggregated_ai_input_data["assessments_data"].append(assessment_data)

        logger.info(f"Aggregation completed for User {user.id}, Package {package.id}.")
        return aggregated_ai_input_data

    except Exception as e:
        error_msg = f"Failed to aggregate package data for AI (User: {user.id}, Package: {package.id}): {e}"
        logger.exception(error_msg)
        # Depending on how this service is called, you might re-raise or return an error indicator
        # For now, returning None signifies failure.
        return None
