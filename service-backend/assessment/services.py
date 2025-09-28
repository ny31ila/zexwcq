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
        elif assessment.name.lower() == "disc":
             calculated_results = _calculate_disc_scores(attempt.raw_results_json)
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

def _calculate_gardner_scores(user_responses):
    """
    Calculate and interpret scores for Gardner's Multiple Intelligences test.
    This function processes raw user responses, calculates scores for each dimension,
    provides interpretations, and ranks the intelligences.
    """
    # Define dimensions and their corresponding question IDs
    dimensions = {
        "linguistic_verbal": {"name": "زبانی-کلامی", "questions": [1, 9, 17, 25, 33, 41, 49, 57, 65, 73]},
        "logical_mathematical": {"name": "منطقی-ریاضی", "questions": [2, 10, 18, 26, 34, 42, 50, 58, 66, 74]},
        "visual_spatial": {"name": "دیداری-فضایی", "questions": [3, 11, 19, 27, 35, 43, 51, 59, 67, 75]},
        "bodily_kinesthetic": {"name": "بدنی-جنبشی", "questions": [4, 12, 20, 28, 36, 44, 52, 60, 68, 76]},
        "interpersonal": {"name": "میان فردی", "questions": [5, 13, 21, 29, 37, 45, 53, 61, 69, 77]},
        "intrapersonal": {"name": "درون فردی", "questions": [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]},
        "musical": {"name": "موسیقیایی", "questions": [7, 15, 23, 31, 39, 47, 55, 63, 71, 79]},
        "naturalist": {"name": "طبیعت گرا", "questions": [8, 16, 24, 32, 40, 48, 56, 64, 72, 80]}
    }

    # --- 1. Validate and Sanitize Input ---
    if not isinstance(user_responses, dict):
        return {"status": "error", "message": "Invalid format: Responses must be a dictionary."}

    # Expects string keys and string values, converts to integers
    validated_responses = {}
    for q_id_str, answer_str in user_responses.items():
        try:
            q_id = int(q_id_str)
            answer = int(answer_str)
            if not (1 <= answer <= 5):
                raise ValueError("Answer out of range")
            validated_responses[q_id] = answer
        except (ValueError, TypeError):
            return {"status": "error", "message": f"Invalid response data for question '{q_id_str}'."}

    # Check for completeness
    all_required_questions = {q for dim_info in dimensions.values() for q in dim_info["questions"]}
    missing_questions = sorted(list(all_required_questions - set(validated_responses.keys())))
    if missing_questions:
        return {"status": "error", "message": f"Missing responses for questions: {missing_questions}"}

    # --- 2. Calculate Scores ---
    scores = {}
    total_score = 0
    for dim_id, dim_info in dimensions.items():
        dim_score = sum(validated_responses[q_id] for q_id in dim_info["questions"])
        scores[dim_id] = dim_score
        total_score += dim_score

    # --- 3. Interpret Scores ---
    interpretations = {}
    for dim_id, score in scores.items():
        if score <= 20: # Adjusted based on 10 questions per dimension (10-50 range)
            interpretations[dim_id] = "ضعیف"
        elif score <= 35:
            interpretations[dim_id] = "متوسط"
        else:
            interpretations[dim_id] = "قوی"

    if total_score <= 160:
        total_interpretation = "هوش چندگانه فرد ضعیف است."
    elif total_score <= 240:
        total_interpretation = "هوش چندگانه فرد متوسط است."
    else:
        total_interpretation = "هوش چندگانه فرد بالا است."

    # --- 4. Calculate Percentages ---
    # Max score per dimension is 10 questions * 5 points = 50
    percentages = {dim_id: round((score / 50) * 100, 2) for dim_id, score in scores.items()}

    # --- 5. Rank Intelligences ---
    ranked_intelligences = sorted(
        [
            {
                "dimension_id": dim_id,
                "dimension_name": dimensions[dim_id]["name"],
                "score": score,
                "percentage": percentages[dim_id],
                "interpretation": interpretations[dim_id]
            }
            for dim_id, score in scores.items()
        ],
        key=lambda x: (-x['score'], x['dimension_id']) # Sort by score desc, then name asc for ties
    )

    # --- 6. Identify Strongest and Weakest ---
    if not scores: # Should not happen if validation is correct
        strongest_intelligences = []
        weakest_intelligences = []
    else:
        max_score = max(scores.values())
        min_score = min(scores.values())
        strongest_ids = {dim_id for dim_id, score in scores.items() if score == max_score}
        weakest_ids = {dim_id for dim_id, score in scores.items() if score == min_score}

        strongest_intelligences = [item for item in ranked_intelligences if item["dimension_id"] in strongest_ids]
        weakest_intelligences = [item for item in ranked_intelligences if item["dimension_id"] in weakest_ids]

    # --- 7. Assemble Final Result ---
    return {
        "status": "success",
        "raw_scores": scores,
        "total_score": total_score,
        "interpretations": interpretations,
        "total_interpretation": total_interpretation,
        "percentages": percentages,
        "ranked_intelligences": ranked_intelligences,
        "strongest_intelligences": strongest_intelligences,
        "weakest_intelligences": weakest_intelligences,
    }

# --- Future Expansion Point ---
# def _calculate_adhd_scores(raw_data):
#     """Logic for Swanson ADHD assessment."""
#     pass

# def _calculate_neo_scores(raw_data):
#     """Logic for NEO Personality Inventory."""
#     pass

def _calculate_disc_scores(responses):
    """
    Calculate DISC scores from responses and provide a comprehensive analysis.
    This function is self-contained and consolidates all DISC-related logic.
    """

    # --- Nested Helper Function: Generate Stress Recommendations ---
    def _generate_stress_recommendations(stress_level, significant_differences):
        recommendations = []
        if stress_level == "کم":
            recommendations.append("رفتار شما در اکثر موقعیت‌ها طبیعی و مؤثر است.")
        elif stress_level == "متوسط":
            recommendations.append("توجه به تعادل بین نیازهای شخصی و انتظارات محیطی.")
            for diff in significant_differences:
                dim = diff["dimension"]
                if dim == "D": recommendations.append("توجه به تعادل بین رهبری و همکاری.")
                elif dim == "I": recommendations.append("مدیریت انرژی اجتماعی و زمان‌های تنهایی.")
                elif dim == "S": recommendations.append("یافتن تعادل بین ثبات و انطباق با تغییرات.")
                elif dim == "C": recommendations.append("تعادل بین کمال‌گرایی و عملکرد مؤثر.")
        else:  # بالا
            recommendations.append("بررسی محیط کاری و شناسایی منابع فشار.")
            recommendations.append("مشاوره با متخصص برای مدیریت استرس.")
        return recommendations

    # --- Nested Helper Function: Analyze Profile Differences for Stress ---
    def _analyze_profile_differences(adaptive_scores, natural_scores):
        differences = {dim: abs(adaptive_scores[dim] - natural_scores[dim]) for dim in adaptive_scores}
        total_difference = sum(differences.values())
        significant_differences = [
            {"dimension": dim, "difference": diff, "adaptive_score": adaptive_scores[dim], "natural_score": natural_scores[dim]}
            for dim, diff in differences.items() if diff >= 3
        ]

        if total_difference <= 8:
            stress_level = "کم"
        elif total_difference <= 16:
            stress_level = "متوسط"
        else:
            stress_level = "بالا"

        return {
            "total_difference": total_difference,
            "dimension_differences": differences,
            "significant_differences": significant_differences,
            "stress_level": stress_level,
            "recommendations": _generate_stress_recommendations(stress_level, significant_differences)
        }

    # --- Nested Helper Function: Determine Profile Type ---
    def _determine_profile_type(scores, dominant_types, profile_type):
        sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_dims[0][0]
        secondary = sorted_dims[1][0] if len(sorted_dims) > 1 else None

        profile_mappings = {
            "D": {"name": "پیروز (Winner)", "description": "قاطع، ریسک‌پذیر، تمرکز بر نتیجه"},
            "I": {"name": "مشتاق (Enthusiast)", "description": "تمایل به صحبت و شنیدن، خلاق و پویا"},
            "S": {"name": "صلح‌بان (Peacekeeper)", "description": "حفظ ثبات در شرایط سخت، شنونده عالی"},
            "C": {"name": "تحلیل‌گر (Analyst)", "description": "انگیزه بر درستی کارها، تحلیل‌گر، دقیق"},
            "DC": {"name": "چالش‌گر (Challenger)", "description": "تمایل به نتیجه‌گرایی و دقت بالا، خلاق و پرشور"},
            "Di": {"name": "جستجوگر (Seeker)", "description": "پرهیجان، علاقه‌مند به شکستن مرزها"},
            "iD": {"name": "ریسک‌پذیر (Risk Taker)", "description": "معتقد به ریسک کردن، با اعتماد به نفس و حمایت‌گر"},
            "iS": {"name": "رفیق (Buddy)", "description": "صلح‌جو، بخشنده، با اعتماد به نفس"},
            "Si": {"name": "همکار (Collaborator)", "description": "مهارت در تیم‌سازی، محبوب"},
            "SC": {"name": "کاردان (Technician)", "description": "قابل اعتماد و توانا، نیاز به محیط آرام"},
            "CS": {"name": "پایه (Bedrock)", "description": "باثبات و متواضع، تمرکز بر پیش‌بینی اتفاقات"},
            "CD": {"name": "کمال‌گرا (Perfectionist)", "description": "تمایل به بهترین بودن، ذهنیتی روشن و تحلیلی"}
        }

        profile_key = primary
        # Check for combination profiles
        if len(dominant_types) > 1 and secondary and abs(scores[primary] - scores[secondary]) <= 2:
            combo_key = "".join(sorted([primary, secondary]))
            profile_key = combo_key if combo_key in profile_mappings else primary

        profile_info = profile_mappings.get(profile_key, {"name": f"غالب {primary}", "description": "پروفایل ترکیبی"})
        return {
            "type": profile_key, "name": profile_info["name"], "description": profile_info["description"],
            "primary_dimension": primary, "secondary_dimension": secondary, "profile_context": profile_type
        }

    # --- Main Function Logic ---
    EXPECTED_QUESTIONS = 24
    if not isinstance(responses, dict):
        return {"success": False, "error": "INVALID_FORMAT", "message": "Responses must be a dictionary."}
    if len(responses) != EXPECTED_QUESTIONS:
        return {"success": False, "error": "INCOMPLETE_RESPONSES", "message": f"Expected {EXPECTED_QUESTIONS} responses, received {len(responses)}."}

    most_like_counts = {"D": 0, "I": 0, "S": 0, "C": 0}
    least_like_counts = {"D": 0, "I": 0, "S": 0, "C": 0}
    valid_types = {"D", "I", "S", "C"}

    for q_id, resp_data in responses.items():
        if not isinstance(resp_data, dict) or not all(k in resp_data for k in ["most_like_me", "least_like_me"]):
            return {"success": False, "error": "MISSING_RESPONSE_KEYS", "message": f"Question {q_id} is missing required keys."}

        most_like, least_like = resp_data["most_like_me"], resp_data["least_like_me"]
        if most_like not in valid_types or least_like not in valid_types or most_like == least_like:
            return {"success": False, "error": "INVALID_DISC_VALUE", "message": f"Invalid values for question {q_id}."}

        most_like_counts[most_like] += 1
        least_like_counts[least_like] += 1

    # Calculate scores for the three profiles
    adaptive_scores = most_like_counts
    natural_scores = least_like_counts
    perceived_scores = {dim: most_like_counts[dim] - least_like_counts[dim] for dim in valid_types}

    # Determine dominant types
    adaptive_dominant = [dim for dim, score in adaptive_scores.items() if score == max(adaptive_scores.values())]
    natural_dominant = [dim for dim, score in natural_scores.items() if score == max(natural_scores.values())]
    perceived_dominant = [dim for dim, score in perceived_scores.items() if score == max(perceived_scores.values())]

    # Generate profile interpretations using nested helpers
    adaptive_profile = _determine_profile_type(adaptive_scores, adaptive_dominant, "adaptive")
    natural_profile = _determine_profile_type(natural_scores, natural_dominant, "natural")
    perceived_profile = _determine_profile_type(perceived_scores, perceived_dominant, "perceived")

    # Analyze stress using nested helper
    stress_analysis = _analyze_profile_differences(adaptive_scores, natural_scores)

    return {
        "success": True,
        "raw_scores": {"most_like_counts": most_like_counts, "least_like_counts": least_like_counts},
        "profiles": {
            "adaptive": {"name": "پروفایل تطبیقی (خود عمومی)", "scores": adaptive_scores, "dominant_types": adaptive_dominant, "interpretation": adaptive_profile},
            "natural": {"name": "پروفایل طبیعی (خود غریزی)", "scores": natural_scores, "dominant_types": natural_dominant, "interpretation": natural_profile},
            "perceived": {"name": "خود ادراک‌شده (آیینه)", "scores": perceived_scores, "dominant_types": perceived_dominant, "interpretation": perceived_profile}
        },
        "stress_analysis": stress_analysis,
        "final_behavioral_style": perceived_profile
    }

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
