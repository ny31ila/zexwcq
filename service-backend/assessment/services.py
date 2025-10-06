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
import re
from collections import defaultdict

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
    calculated_results = {}
    try:
        if assessment.name.lower() == "mbti":
            calculated_results = _calculate_mbti_scores(attempt.raw_results_json)
        elif assessment.name.lower() == "holland":
             calculated_results = _calculate_holland_scores(attempt.raw_results_json)
        elif assessment.name.lower() == "gardner":
             calculated_results = _calculate_gardner_scores(attempt.raw_results_json)
        elif assessment.name.lower() == "disc":
             calculated_results = _calculate_disc_scores(attempt.raw_results_json)
        else:
            # Generic handler or log unsupported assessment
            logger.info(f"No specific calculator implemented for assessment '{assessment.name}'. Using generic processor.")
            total_questions_answered = len(attempt.raw_results_json.keys()) if isinstance(attempt.raw_results_json, dict) else 0
            calculated_results = {
                "generic_summary": {
                    "assessment_name": assessment.name,
                    "total_questions_answered": total_questions_answered,
                    "processed_at": timezone.now().isoformat()
                }
            }

        # 4. --- Save Calculated Results ---
        attempt.processed_results_json = calculated_results
        attempt.save(update_fields=['processed_results_json', 'updated_at'])

        success_msg = f"Score calculation completed and saved for Attempt {attempt_id} ({assessment.name})."
        logger.info(success_msg)
        return {'status': 'success', 'message': success_msg}

    except Exception as e:
        error_msg = f"Failed to calculate scores for Attempt {attempt_id} ({assessment.name}): {e}"
        logger.exception(error_msg)
        return {'status': 'error', 'message': error_msg}


# --- Helper Functions for Specific Assessments ---

def _calculate_mbti_scores(raw_data):
    """
    Calculate and interpret scores for the MBTI assessment.
    This function is self-contained and includes all necessary data and logic,
    with robust handling for tied results.
    """
    # --- Nested Data Structures for MBTI Test ---
    # This map is based on the corrected mbti.json file.
    QUESTION_MAP = {
        "1": {"a": "I", "b": "E"}, "2": {"a": "S", "b": "N"}, "3": {"a": "T", "b": "F"}, "4": {"a": "P", "b": "J"},
        "5": {"a": "I", "b": "E"}, "6": {"a": "S", "b": "N"}, "7": {"a": "T", "b": "F"}, "8": {"a": "P", "b": "J"},
        "9": {"a": "I", "b": "E"}, "10": {"a": "S", "b": "N"}, "11": {"a": "T", "b": "F"}, "12": {"a": "P", "b": "J"},
        "13": {"a": "I", "b": "E"}, "14": {"a": "S", "b": "N"}, "15": {"a": "T", "b": "F"}, "16": {"a": "P", "b": "J"},
        "17": {"a": "I", "b": "E"}, "18": {"a": "S", "b": "N"}, "19": {"a": "T", "b": "F"}, "20": {"a": "P", "b": "J"},
        "21": {"a": "I", "b": "E"}, "22": {"a": "S", "b": "N"}, "23": {"a": "T", "b": "F"}, "24": {"a": "P", "b": "J"},
        "25": {"a": "I", "b": "E"}, "26": {"a": "S", "b": "N"}, "27": {"a": "T", "b": "F"}, "28": {"a": "P", "b": "J"},
        "29": {"a": "I", "b": "E"}, "30": {"a": "S", "b": "N"}, "31": {"a": "T", "b": "F"}, "32": {"a": "P", "b": "J"},
        "33": {"a": "I", "b": "E"}, "34": {"a": "S", "b": "N"}, "35": {"a": "T", "b": "F"}, "36": {"a": "P", "b": "J"},
        "37": {"a": "I", "b": "E"}, "38": {"a": "S", "b": "N"}, "39": {"a": "T", "b": "F"}, "40": {"a": "P", "b": "J"},
        "41": {"a": "I", "b": "E"}, "42": {"a": "S", "b": "N"}, "43": {"a": "T", "b": "F"}, "44": {"a": "P", "b": "J"},
        "45": {"a": "I", "b": "E"}, "46": {"a": "S", "b": "N"}, "47": {"a": "T", "b": "F"}, "48": {"a": "P", "b": "J"},
        "49": {"a": "I", "b": "E"}, "50": {"a": "S", "b": "N"}, "51": {"a": "T", "b": "F"}, "52": {"a": "P", "b": "J"},
        "53": {"a": "I", "b": "E"}, "54": {"a": "S", "b": "N"}, "55": {"a": "T", "b": "F"}, "56": {"a": "P", "b": "J"},
        "57": {"a": "I", "b": "E"}, "58": {"a": "S", "b": "N"}, "59": {"a": "T", "b": "F"}, "60": {"a": "P", "b": "J"}
    }
    DIMENSION_INTERPRETATIONS = {
        "I": {"name": "درون‌گرا (Introvert - I)", "description": "افرادی که درون‌گرایی را ترجیح می‌دهند، تمایل دارند روی تجربیات و عقاید دنیای درونی خود تمرکز کنند و از افکار، احساسات و اندیشه‌های درونی خود انرژی می‌گیرند."},
        "E": {"name": "برون‌گرا (Extravert - E)", "description": "افرادی که برون‌گرایی را ترجیح می‌دهند، تمایل دارند بر دنیای بیرونی و افراد و رویدادهای خارجی تمرکز کنند و از رویدادها، تجربه‌ها و تعاملات بیرونی انرژی می‌گیرند."},
        "S": {"name": "حسی (Sensing - S)", "description": "افرادی که ترجیح می‌دهند با استفاده از حواس پنج‌گانه به آنچه در اطرافشان می‌گذرد پی ببرند و به حقایق عملی یک موقعیت توجه می‌کنند."},
        "N": {"name": "شهودی (Intuiting - N)", "description": "افرادی که ترجیح می‌دهند با دیدن تصویر بزرگ و تمرکز بر پیوندها و ارتباطات میان حقایق، اطلاعات را درک کنند و در دیدن امکانات جدید و خلاقیت بینش خوبی دارند."},
        "T": {"name": "تفکری (Thinking - T)", "description": "افرادی که در تصمیم‌گیری به نتایج منطقی انتخاب یا عمل توجه دارند و بی‌طرفانه و به شکل عینی، علت و معلول را تجزیه و تحلیل می‌کنند."},
        "F": {"name": "احساسی (Feeling - F)", "description": "افرادی که به احساسات دیگران توجه می‌کنند، نیازها و ارزش‌ها را درک کرده و احساساتشان را نشان می‌دهند."},
        "J": {"name": "منضبط (Judging - J)", "description": "این افراد سبک زندگی ساختاری و سازمان‌یافته دارند و دوست دارند هر چیزی در جای خود قرار گیرد."},
        "P": {"name": "ملاحظه‌کار (Perceiving - P)", "description": "این افراد انطباق‌پذیر و انعطاف‌پذیر هستند و زندگی خود را با توجه به شرایطی که پیش می‌آید، تنظیم و اداره می‌کنند."}
    }
    TYPE_DESCRIPTIONS = {
        "ISTJ": {"name": "بازرس", "description": "جدی، آرام، واقع‌گرا، منظم و منطقی. موفقیت را با تمرکز و پشتکار بدست می‌آورد. مسئولیت‌پذیر است و کارها را بدون توجه به معطلی انجام می‌دهد."},
        "ISFJ": {"name": "محافظ", "description": "آرام، خوش‌برخورد، مسئولیت‌پذیر و وظیفه‌شناس. برای انجام وظایف خالصانه کار می‌کند. دقیق، زحمت‌کش، وفادار و نسبت به احساسات دیگران بسیار حساس است."},
        "INFJ": {"name": "حامی", "description": "موفقیت را با پشتکار فراوان بدست می‌آورد و در انجام کارها اشتیاق دارد. آرام، با قدرت و وظیفه‌شناس است. به کمک به دیگران علاقه دارد و مورد احترام مردم است."},
        "INTJ": {"name": "معمار", "description": "افکاری بدیع و مبتکرانه دارد و پرانرژی است. قدرت خاصی در سازماندهی کارها دارد و می‌تواند کارها را با کمک یا بدون کمک دیگران به پایان برساند. منتقد، مستقل، مصمم و گاهی لجوج است."},
        "ISTP": {"name": "صنعتگر", "description": "افرادی با نگاه نافذ، آرام و محتاط که زندگی را با کنجکاوی تجزیه و تحلیل می‌کنند. علاقه‌مند به اصول علمی، علت و معلول و موضوعات فنی هستند."},
        "ISFP": {"name": "هنرمند", "description": "خستگی‌ناپذیر، خوش‌برخورد، حساس و کم‌ادعا در مورد توانایی‌های خود. از مخالفت پرهیز می‌کند و ارزش‌های خود را به دیگران تحمیل نمی‌کند. اغلب دنباله‌روی وفاداری است و از زمان حال لذت می‌برد."},
        "INFP": {"name": "واسطه", "description": "پر از وفاداری و هواخواهی پرحرارت. علاقه فراوانی به یادگیری، ایده‌های جدید و زبان دارد. گاهی بیش از حد مسئولیت قبول می‌کند و آن را به پایان می‌رساند."},
        "INTP": {"name": "منطق‌دان", "description": "آرام و تودار. در آزمون‌های آموزشی بخصوص در زمینه علمی و تئوری موفق است. به ایده‌ها و نظریات جدید علاقه نشان می‌دهد و به محافل اجتماعی یا بحث‌های بیهوده توجهی ندارد."},
        "ESTP": {"name": "کارآفرین", "description": "واقع‌گرا و بندرت نگران می‌شود. از هرچه پیش آید لذت می‌برد. به ورزش و موضوعات فنی علاقه نشان می‌دهد و در محافل مختلف شرکت می‌کند."},
        "ESFP": {"name": "بازیگر", "description": "برون‌گرا، زودجوش، مهمان‌نواز و خوش‌برخورد. علاقه زیادی به لذت بردن از زمان حال دارد. به ورزش و تولید و ساخت علاقه دارد و برای حقایق اهمیت بیشتری نسبت به تئوری‌های پیچیده قائل است."},
        "ENFP": {"name": "مبارز", "description": "پر حرارت، پرانرژی، دارای قوه تخیل بالا و مبتکر. توانایی انجام هر کاری که به آن علاقه‌مند است را دارد. در پیدا کردن راه‌حل برای هر مشکلی سریع عمل می‌کند و آماده کمک به دیگران است."},
        "ENTP": {"name": "مناظره‌گر", "description": "صریح، بی‌ریا، پرهیجان، پرحرف و باهوش. در پیدا کردن راه‌حل‌های مبتکرانه برای موضوعات پیچیده مهارت دارد. از انجام کارهای یکنواخت روزانه سرباز می‌زند."},
        "ESTJ": {"name": "مجری", "description": "واقع‌بین، قاطع و کم‌احساس. در زمینه تجارت و کارهای فنی استعداد خاصی از خود نشان می‌دهد. به سازماندهی و هدایت فعالیت‌ها و پروژه‌ها علاقه دارد."},
        "ESFJ": {"name": "سفیر", "description": "خوش‌قلب، خوش‌صحبت، محبوب و مسئولیت‌پذیر. از سنین پایین مشارکت و همکاری با دیگران را به خوبی یاد می‌گیرد. همیشه می‌خواهد یک کار نیک برای دیگران انجام دهد و نیاز به تشویق و قدردانی دارد."},
        "ENFJ": {"name": "قهرمان", "description": "مسئولیت‌پذیر و دلسوز. حساسیت واقعی نسبت به آنچه دیگران می‌خواهند، فکر می‌کنند و دارند. در ارائه یک موضوع یا رهبری یک بحث گروهی توانایی خاصی دارد. زودجوش، محبوب و فعال در امور آموزشی است."},
        "ENTJ": {"name": "فرمانده", "description": "پرنشاط، صادق و موفق در مطالعات و آموزش تحصیلی. قدرت رهبری در فعالیت‌های مختلف دارد. معمولاً در کارهایی که نیاز به منطق زیاد و بیان هوشیارانه دارد موفق است."}
    }

    # --- Nested Helper Functions for Interpretation ---
    def get_dimension_interpretation(pref, d1, d2):
        if "/" not in pref:
            return DIMENSION_INTERPRETATIONS[pref]
        else:
            return {
                "name": f"{DIMENSION_INTERPRETATIONS[d1]['name']} / {DIMENSION_INTERPRETATIONS[d2]['name']} (متعادل)",
                "description": "شما خصوصیاتی از هر دو ترجیح را نشان می‌دهید که نشانگر انعطاف‌پذیری در این بعد شخصیتی است.",
                "details": {
                    d1: DIMENSION_INTERPRETATIONS[d1],
                    d2: DIMENSION_INTERPRETATIONS[d2]
                }
            }

    def get_type_interpretation(mbti_type, preferences):
        pure_type = "".join(p[0] for p in preferences if '/' not in p)
        if "-" not in mbti_type and pure_type in TYPE_DESCRIPTIONS:
             return TYPE_DESCRIPTIONS[pure_type]
        else:
            # Build a dynamic description for tied types
            desc_parts = [DIMENSION_INTERPRETATIONS[p.split('/')[0]]['name'].split(" ")[0] for p in preferences]
            return {
                "name": "تیپ شخصیتی ترکیبی",
                "description": f"نتیجه آزمون شما نشان‌دهنده تعادل در برخی از ابعاد شخصیتی است. این تیپ ترکیبی از ترجیحات {', '.join(desc_parts)} است. این تعادل می‌تواند نشان‌دهنده انعطاف‌پذیری شما در موقعیت‌های مختلف باشد."
            }

    # --- Main function logic starts here ---
    try:
        if not isinstance(raw_data, dict):
            logger.warning("MBTI score calculation received invalid raw_data (not a dict).")
            return {"status": "error", "message": "Invalid input data format."}

        scores = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
        for q_id, data in raw_data.items():
            response_option = data.get("response")
            if q_id in QUESTION_MAP and response_option in ['a', 'b']:
                dimension = QUESTION_MAP[q_id][response_option]
                scores[dimension] += 1

        # Determine preferences and handle ties
        result_ei = 'I' if scores['I'] > scores['E'] else ('E' if scores['E'] > scores['I'] else 'I/E')
        result_sn = 'S' if scores['S'] > scores['N'] else ('N' if scores['N'] > scores['S'] else 'S/N')
        result_tf = 'T' if scores['T'] > scores['F'] else ('F' if scores['F'] > scores['T'] else 'T/F')
        result_jp = 'J' if scores['J'] > scores['P'] else ('P' if scores['P'] > scores['J'] else 'J/P')

        preferences = [result_ei, result_sn, result_tf, result_jp]
        mbti_type = "".join(p[0] for p in preferences if '/' not in p)
        if any('/' in p for p in preferences):
             mbti_type = "-".join(preferences)

        # Build the final JSON result
        final_result = {
            "status": "success",
            "mbti_type": mbti_type,
            "scores": scores,
            "preferences": {
                "EI": {"preference": result_ei, "score_I": scores['I'], "score_E": scores['E']},
                "SN": {"preference": result_sn, "score_S": scores['S'], "score_N": scores['N']},
                "TF": {"preference": result_tf, "score_T": scores['T'], "score_F": scores['F']},
                "JP": {"preference": result_jp, "score_J": scores['J'], "score_P": scores['P']}
            },
            "interpretation": {
                "type_details": get_type_interpretation(mbti_type, preferences),
                "dimension_details": {
                    "EI": get_dimension_interpretation(result_ei, 'I', 'E'),
                    "SN": get_dimension_interpretation(result_sn, 'S', 'N'),
                    "TF": get_dimension_interpretation(result_tf, 'T', 'F'),
                    "JP": get_dimension_interpretation(result_jp, 'J', 'P')
                }
            }
        }

        logger.info(f"Successfully calculated MBTI scores. Type: {mbti_type}")
        return final_result

    except Exception as e:
        logger.exception("An unexpected error occurred during MBTI score calculation.")
        return {"status": "error", "message": str(e)}


def _calculate_holland_scores(raw_data):
    """
    Calculates and interprets scores for the Holland (RIASEC) test.

    This function processes raw user responses, calculates scores for each of the
    six RIASEC dimensions, provides detailed interpretations, and determines the
    user's 3-letter Holland code, handling ties correctly.

    Args:
        raw_data (dict): The raw_results_json from a UserAssessmentAttempt.

    Returns:
        dict: A dictionary containing the detailed analysis of the test,
              or an error message if the input is invalid.
    """
    # --- Nested Data Structures and Scorer Class for Holland Test ---
    # This data is defined inside the function to keep it self-contained,
    # matching the pattern of other scoring functions in this service module.

    HOLLAND_TEST_STRUCTURE = {
        "dimensions": [
            {"id": "realistic", "name": "واقع‌گرا/اهل کار"},
            {"id": "investigative", "name": "مسئله‌حل‌کن / جستجوگر"},
            {"id": "enterprising", "name": "ترغیب‌کننده / متهور"},
            {"id": "social", "name": "امدادگر / اجتماعی"},
            {"id": "artistic", "name": "خلاق / هنری"},
            {"id": "conventional", "name": "سازمان‌دهنده / متعارف"}
        ],
        "self_assessment_map": {
            "self_assessment_1": {
                1: "realistic", 2: "investigative", 3: "artistic",
                4: "social", 5: "enterprising", 6: "conventional"
            },
            "self_assessment_2": {
                1: "realistic", 2: "investigative", 3: "artistic",
                4: "social", 5: "enterprising", 6: "conventional"
            }
        },
        "interpretation_details": {
          "realistic": { "characteristics": ["اهل عمل","خودمحور","صرفه‌جو","سرسخت","مصر","غیر اجتماعی"], "suitable_occupations": "مشاغل فنی، کشاورزی و بعضی مشاغل خدماتی" },
          "investigative": { "characteristics": ["کنجکاو","دقیق","تحلیل‌گر","پیچیده","کناره‌گیر","منتقد","خوددار"], "suitable_occupations": "مشاغل علمی و پژوهشی، پزشکی و برخی مهندسی‌ها" },
          "enterprising": { "characteristics": ["ماجراجو","با انرژی","مطمئن به خود","هیجان‌طلب","سلطه‌جو"], "suitable_occupations": "مدیریت، تجارت و فروشندگی" },
          "social": { "characteristics": ["اهل همکاری","معاشرتی","صبور","مسئول","صمیمی","امدادگر"], "suitable_occupations": "تعلیم و تربیت، رفاه اجتماعی و مشاغل خدماتی" },
          "artistic": { "characteristics": ["عاطفی","ابرازگر","خیال‌پرداز","شهودی","آرمانگرا","مستقل"], "suitable_occupations": "هنر، موسیقی، ادبیات، بازیگری، ترجمهٔ ادبی" },
          "conventional": { "characteristics": ["محتاط","مطیع","منظم","صرفه‌جو","دوراندیش","وظیفه‌شناس"], "suitable_occupations": "اداری، منشی‌گری، حسابداری، بایگانی" }
        }
    }

    class HollandTestScorer:
        """
        Calculates scores and provides interpretation for the Holland (RIASEC) test.
        This class encapsulates the logic based on the provided Python script and JSON structure.
        """
        def __init__(self, test_structure):
            self.test_structure = test_structure
            self.dimensions = [dim['id'] for dim in test_structure['dimensions']]
            self.dimension_names = {dim['id']: dim['name'] for dim in test_structure['dimensions']}
            self.self_assessment_map = test_structure['self_assessment_map']
            self.interpretation_details = test_structure['interpretation_details']

        def parse_response_key(self, key):
            """Parse response key to extract section and dimension information."""
            # Using five underscores as the separator, as specified.
            checkbox_pattern = r'^(interests|experiences|occupations)_____(realistic|investigative|enterprising|social|artistic|conventional)_____(\d+)$'
            self_assess_pattern = r'^(self_assessment_1|self_assessment_2)_____(\d+)$'

            checkbox_match = re.match(checkbox_pattern, key)
            if checkbox_match:
                section, dimension, question_id = checkbox_match.groups()
                return {'type': 'checkbox', 'dimension': dimension}

            self_assess_match = re.match(self_assess_pattern, key)
            if self_assess_match:
                section, question_id_str = self_assess_match.groups()
                question_id = int(question_id_str)
                # Use the hardcoded map to find the dimension
                dimension = self.self_assessment_map.get(section, {}).get(question_id)
                if dimension:
                    return {'type': 'likert', 'dimension': dimension}
            return None

        def calculate_scores(self, response_data):
            """Calculate scores for all dimensions from the raw response data."""
            scores = {dim: 0 for dim in self.dimensions}
            if not isinstance(response_data, dict):
                return scores # Return zeroed scores if input is invalid

            for key, value in response_data.items():
                parsed = self.parse_response_key(key)
                if not parsed:
                    continue

                response_value = value.get('response')
                if response_value is None:
                    continue

                dimension = parsed['dimension']
                if parsed['type'] == 'checkbox':
                    if response_value is True:
                        scores[dimension] += 1
                elif parsed['type'] == 'likert':
                    try:
                        scores[dimension] += int(response_value)
                    except (ValueError, TypeError):
                        continue
            return scores

        def get_top_dimensions_and_code(self, scores):
            """Get top dimensions, handling ties, and generate the Holland code."""
            dimension_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            if not dimension_scores:
                return [], ""

            # Group dimensions by score to handle ties
            score_groups = defaultdict(list)
            for dim, score in dimension_scores:
                score_groups[score].append(dim)

            # Get the top 3 score levels
            top_scores = sorted(score_groups.keys(), reverse=True)[:3]

            # Build the ranked list and Holland code simultaneously
            dimension_letters = {'realistic': 'R', 'investigative': 'I', 'artistic': 'A', 'social': 'S', 'enterprising': 'E', 'conventional': 'C'}
            ranked_dimensions = []
            code_parts = []
            rank = 1
            for score in top_scores:
                group = sorted(score_groups[score]) # Sort alphabetically for consistent tie-breaking

                # Add to ranked list
                for dim in group:
                    ranked_dimensions.append({
                        'rank': rank,
                        'dimension': dim,
                        'name': self.dimension_names[dim],
                        'score': scores[dim]
                    })

                # Add to Holland code
                group_letters = [dimension_letters[dim] for dim in group]
                code_parts.append('/'.join(sorted(group_letters)))

                rank += len(group) # Increment rank by the size of the tied group

            return ranked_dimensions, '-'.join(code_parts)

        def interpret_results(self, scores, ranked_dimensions, holland_code):
            """Generate the final interpretation object."""
            return {
                "status": "success",
                "holland_code": holland_code,
                "raw_scores": scores,
                "ranked_dimensions": ranked_dimensions,
                "dimension_details": {
                    dim: {
                        "name": self.dimension_names[dim],
                        "score": scores[dim],
                        "characteristics": self.interpretation_details[dim]["characteristics"],
                        "suitable_occupations": self.interpretation_details[dim]["suitable_occupations"]
                    } for dim in self.dimensions
                }
            }

    # --- Main function logic starts here ---
    try:
        if not isinstance(raw_data, dict):
            logger.warning("Holland score calculation received invalid raw_data (not a dict).")
            return {"status": "error", "message": "Invalid input data format."}

        scorer = HollandTestScorer(HOLLAND_TEST_STRUCTURE)
        scores = scorer.calculate_scores(raw_data)
        ranked_dimensions, holland_code = scorer.get_top_dimensions_and_code(scores)
        result = scorer.interpret_results(scores, ranked_dimensions, holland_code)

        logger.info(f"Successfully calculated Holland scores. Code: {holland_code}")
        return result

    except Exception as e:
        logger.exception("An unexpected error occurred during Holland score calculation.")
        return {"status": "error", "message": str(e)}


def _calculate_gardner_scores(user_responses):
    """
    Calculate and interpret scores for Gardner's Multiple Intelligences test.

    This function processes raw user responses which are expected in a nested
    format, calculates scores for each dimension, provides interpretations,
    and ranks the intelligences.

    Args:
        user_responses (dict): A dictionary of user responses.
            Expected format:
            {
                "1": {"response": "5"},
                "2": {"response": "3"},
                ...
            }
            The keys are question IDs (as strings) and the values are objects
            containing a "response" key with the answer (as a string).

    Returns:
        dict: A dictionary containing the detailed analysis of the test,
              or an error message if the input is invalid.
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

    validated_responses = {}
    for q_id_str, resp_obj in user_responses.items():
        try:
            # Check for the correct nested structure
            if not isinstance(resp_obj, dict) or "response" not in resp_obj:
                raise ValueError("Missing 'response' key in response object.")

            q_id = int(q_id_str)
            answer = int(resp_obj["response"]) # Get answer from the nested object

            if not (1 <= answer <= 5):
                raise ValueError("Answer out of range 1-5.")

            validated_responses[q_id] = answer
        except (ValueError, TypeError):
            return {"status": "error", "message": f"Invalid or malformed response data for question '{q_id_str}'."}

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
        if score <= 20:
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
        key=lambda x: (-x['score'], x['dimension_id'])
    )

    # --- 6. Identify Strongest and Weakest ---
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
    Calculate DISC scores from responses, providing detailed behavioral patterns
    and a simplified stress analysis, structured for frontend consumption.
    """

    # --- Nested Helper: Determine Detailed Behavioral Pattern ---
    def _get_detailed_behavioral_pattern(scores):
        profile_mappings = {
            "D": {"name": "تسلط‌گرا (Dominant) یا برتری‌طلب (پیروز)", "description": "غلبه بر چالش‌ها، تمرکز بر نتیجه، قاطع و صریح، اعتماد به نفس بالا. نیاز به یادگیری صبر و توجه به جزئیات."},
            "I": {"name": "تأثیرگذار (Influent, Enthusiast) یا متقاعدکننده (مشتاق)", "description": "پیشگام، متقاعدکننده، پرشور، خوش‌بین، خلاق، پویا، تمایل به بودن با گروه. نیاز به تقویت توانایی تحقیق و پیگیری و همچنین کنترل شور و هیجان."},
            "S": {"name": "باثبات (Steady, Peacemaker) یا حامی (صلح‌بان)", "description": "آرام، صبور، سازگار، حمایت‌کننده. تمایل به حفظ وضعیت موجود. نیاز به انطباق با تغییرات و چندکارگی."},
            "C": {"name": "وظیفه‌شناس (Conscientious) یا تحلیل‌گر", "description": "کار با کیفیت و دقت بالا، مستقل، محافظه‌کار. نیاز به قدرت سازش و تصمیم‌گیری سریع."},
            "DC": {"name": "چالش‌گر (Challenger)", "description": "ترکیبی از تسلط و وظیفه‌شناسی. تمایل به نتیجه‌گرایی و دقت بالا، خلاق و پرشور، نیاز به توجه بیشتر به روابط."},
            "DI": {"name": "جستجوگر (Seeker)", "description": "ترکیب تسلط‌گرا و تأثیرگذار، پرهیجان، علاقه‌مند به شکستن مرزها. نیاز به کنترل بیشتر."},
            "ID": {"name": "ریسک‌پذیر (Risk Taker)", "description": "ترکیب تأثیرگذار و تسلط‌گرا. معتقد به ریسک کردن، با اعتماد به نفس و حمایت‌گر. نیاز به مدیریت ناامیدی."},
            "IS": {"name": "رفیق (Buddy)", "description": "ترکیب تأثیرگذار و باثبات. صلح‌جو، بخشنده، با اعتماد به نفس. نیاز به قاطعیت و عدم سلطه‌پذیری."},
            "SI": {"name": "همکار (Collaborator)", "description": "ترکیب باثبات و تأثیرگذار. مهارت در تیم‌سازی، محبوب. نیاز به حفظ تمرکز."},
            "SC": {"name": "کاردان (Technician)", "description": "ترکیب باثبات و وظیفه‌شناس. قابل اعتماد و توانا، نیاز به محیط آرام. ممکن است گوشه‌گیر."},
            "CS": {"name": "پایه (Bedrock)", "description": "ترکیب وظیفه‌شناس و باثبات. باثبات و متواضع، تمرکز بر پیش‌بینی اتفاقات. نیاز به دایره ارتباطی گسترده."},
            "CD": {"name": "کمال‌گرا (Perfectionist)", "description": "ترکیب وظیفه‌شناس و تسلط‌گرا. تمایل به بهترین بودن، ذهنیتی روشن و تحلیلی. نیاز به همدلی."}
        }

        sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_dim, primary_score = sorted_dims[0]
        secondary_dim, secondary_score = sorted_dims[1]

        if primary_score - secondary_score <= 2:
            profile_key = "".join(sorted([primary_dim, secondary_dim]))
        else:
            profile_key = primary_dim

        # Fallback for keys like 'i' or 'd' if they appear in user data
        profile_key_upper = profile_key.upper()
        pattern = profile_mappings.get(profile_key_upper, profile_mappings.get(primary_dim))
        return {"id": profile_key_upper, "name": pattern["name"], "description": pattern["description"]}

    # --- Nested Helper: Simplified Stress Analysis ---
    def _analyze_stress_levels(adaptive_scores, natural_scores):
        STRESS_THRESHOLD = 10
        total_difference = sum(abs(adaptive_scores[dim] - natural_scores[dim]) for dim in adaptive_scores)

        if total_difference > STRESS_THRESHOLD:
            stress_level = "زیاد"
            interpretation = "فرد در تلاش مداوم برای انطباق رفتار ذاتی خود با دنیای بیرون (مانند محیط کار) است. این موضوع می‌تواند منجر به استرس زیادی در زندگی شده و روشی نامناسب برای همکاری با دیگران و زندگی کردن باشد."
        else:
            stress_level = "کم"
            interpretation = "سطح انطباق‌پذیری فرد با محیط در حد طبیعی است و نشان‌دهنده عدم وجود فشار یا استرس قابل توجهی برای تغییر رفتار ذاتی است."

        return {"level": stress_level, "score": total_difference, "interpretation": interpretation}

    # --- Main Function Logic ---
    EXPECTED_QUESTIONS = 24
    if not isinstance(responses, dict) or len(responses) != EXPECTED_QUESTIONS:
        return {"success": False, "error": "INCOMPLETE_OR_INVALID_FORMAT", "message": f"Expected {EXPECTED_QUESTIONS} responses in a dictionary."}

    most_like_counts = {"D": 0, "I": 0, "S": 0, "C": 0}
    least_like_counts = {"D": 0, "I": 0, "S": 0, "C": 0}
    valid_types = {"D", "I", "S", "C"}

    for q_id, resp_data in responses.items():
        if not isinstance(resp_data, dict) or "most_like_me" not in resp_data or "least_like_me" not in resp_data:
            return {"success": False, "error": "MISSING_RESPONSE_KEYS", "message": f"Question {q_id} is missing keys."}

        most_like, least_like = resp_data["most_like_me"].upper(), resp_data["least_like_me"].upper()
        if most_like not in valid_types or least_like not in valid_types or most_like == least_like:
            return {"success": False, "error": "INVALID_DISC_VALUE", "message": f"Invalid values for question {q_id}."}

        most_like_counts[most_like] += 1
        least_like_counts[least_like] += 1

    adaptive_scores = most_like_counts
    natural_scores = least_like_counts
    perceived_scores = {dim: most_like_counts[dim] - least_like_counts[dim] for dim in valid_types}

    final_behavioral_pattern = _get_detailed_behavioral_pattern(perceived_scores)
    stress_analysis = _analyze_stress_levels(adaptive_scores, natural_scores)

    return {
        "success": True,
        "final_behavioral_pattern": final_behavioral_pattern,
        "stress_analysis": stress_analysis,
        "profiles": {
            "adaptive": {"name": "پروفایل تطبیقی (خود عمومی - نقاب)", "description": "Represents behavior in professional/social environments.", "scores": adaptive_scores},
            "natural": {"name": "پروفایل طبیعی (خود غریزی - ذات)", "description": "Reflects instinctive behavior, especially under pressure.", "scores": natural_scores},
            "perceived": {"name": "خود ادراک‌شده (برآیند نقاب و ذات - آیینه)", "description": "A composite profile used to determine the final behavioral pattern.", "scores": perceived_scores}
        }
    }


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
        return None