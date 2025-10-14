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
        elif assessment.name.lower() == "neo":
            calculated_results = _calculate_neo_scores(attempt.raw_results_json)
        elif assessment.name.lower() == "pvq":
            calculated_results = _calculate_pvq_scores(attempt.raw_results_json)
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

def _calculate_neo_scores(raw_data):
    """
    Calculates and interprets scores for the NEO-FFI (Five-Factor Inventory) assessment.

    This function processes raw user responses to calculate scores for the five core
    personality dimensions (Neuroticism, Extraversion, Openness, Agreeableness, Conscientiousness).
    It then derives 10 detailed "personality styles" based on the interplay between these
    dimensions, providing a comprehensive, multi-layered analysis.

    The final output is a rich JSON object designed for easy consumption by the frontend,
    including raw and scaled scores, descriptive levels, strength percentages, and detailed
    interpretations for both dimensions and styles.

    Args:
        raw_data (dict): The raw_results_json from a UserAssessmentAttempt.
            Expected format: {"1": {"response": "4"}, "2": {"response": "1"}, ...}

    Returns:
        dict: A dictionary containing the detailed analysis of the test,
              or an error message if the input is invalid or incomplete.
    """
    # --- Self-Contained Data Structures for NEO-FFI ---
    QUESTIONS_DATA = [
        {"id": 1, "dimension_id": "neuroticism", "is_reverse_scored": True},
        {"id": 2, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 3, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 4, "dimension_id": "agreeableness", "is_reverse_scored": False},
        {"id": 5, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 6, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 7, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 8, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 9, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 10, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 11, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 12, "dimension_id": "extraversion", "is_reverse_scored": True},
        {"id": 13, "dimension_id": "openness", "is_reverse_scored": False},
        {"id": 14, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 15, "dimension_id": "conscientiousness", "is_reverse_scored": True},
        {"id": 16, "dimension_id": "neuroticism", "is_reverse_scored": True},
        {"id": 17, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 18, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 19, "dimension_id": "agreeableness", "is_reverse_scored": False},
        {"id": 20, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 21, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 22, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 23, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 24, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 25, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 26, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 27, "dimension_id": "extraversion", "is_reverse_scored": True},
        {"id": 28, "dimension_id": "openness", "is_reverse_scored": False},
        {"id": 29, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 30, "dimension_id": "conscientiousness", "is_reverse_scored": True},
        {"id": 31, "dimension_id": "neuroticism", "is_reverse_scored": True},
        {"id": 32, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 33, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 34, "dimension_id": "agreeableness", "is_reverse_scored": False},
        {"id": 35, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 36, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 37, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 38, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 39, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 40, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 41, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 42, "dimension_id": "extraversion", "is_reverse_scored": True},
        {"id": 43, "dimension_id": "openness", "is_reverse_scored": False},
        {"id": 44, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 45, "dimension_id": "conscientiousness", "is_reverse_scored": True},
        {"id": 46, "dimension_id": "neuroticism", "is_reverse_scored": True},
        {"id": 47, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 48, "dimension_id": "openness", "is_reverse_scored": True},
        {"id": 49, "dimension_id": "agreeableness", "is_reverse_scored": False},
        {"id": 50, "dimension_id": "conscientiousness", "is_reverse_scored": False},
        {"id": 51, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 52, "dimension_id": "extraversion", "is_reverse_scored": False},
        {"id": 53, "dimension_id": "openness", "is_reverse_scored": False},
        {"id": 54, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 55, "dimension_id": "conscientiousness", "is_reverse_scored": True},
        {"id": 56, "dimension_id": "neuroticism", "is_reverse_scored": False},
        {"id": 57, "dimension_id": "extraversion", "is_reverse_scored": True},
        {"id": 58, "dimension_id": "openness", "is_reverse_scored": False},
        {"id": 59, "dimension_id": "agreeableness", "is_reverse_scored": True},
        {"id": 60, "dimension_id": "conscientiousness", "is_reverse_scored": False}
    ]

    DIMENSIONS_META = {
        "openness": {"name": "تجربه‌پذیری (Openness)", "abbr": "O", "description": "میزان گشودگی ذهن، علاقه به تجربه‌های جدید، خلاقیت و تفکر انتزاعی."},
        "conscientiousness": {"name": "وظیفه‌شناسی (Conscientiousness)", "abbr": "C", "description": "میزان نظم، برنامه‌ریزی، پشتکار و مسئولیت‌پذیری در انجام وظایف."},
        "extraversion": {"name": "برون‌گرایی (Extraversion)", "abbr": "E", "description": "میزان انرژی اجتماعی، تمایل به تعامل با دیگران و واکنش به محرک‌های خارجی."},
        "agreeableness": {"name": "سازگاری (Agreeableness)", "abbr": "A", "description": "میزان مهربانی، همکاری، اعتماد و تمایل به اجتناب از تعارض."},
        "neuroticism": {"name": "روان‌رنجوری (Neuroticism)", "abbr": "N", "description": "میزان حساسیت به استرس، اضطراب، نگرانی و نوسانات خلقی."}
    }

    PERSONALITY_STYLES_META = {
        "well_being": {"style_name": "سبک بهزیستی (Style Of Well-Being)", "factors": ["neuroticism", "extraversion"], "axes": {"vertical": "neuroticism", "horizontal": "extraversion"}, "types": {
            "N+E-": {"name": "غمگین و بدبین (Gloomy Pessimists)", "condition": "روان‌رنجوری بالا و برون‌گرایی پایین", "detailed_description": "این افراد نیمه خالی لیوان را می‌بینند، به‌سختی خوشحال می‌شوند و با کوچک‌ترین چیزی احساس پریشانی می‌کنند. در شرایط پرفشار و استرس‌زا احساس افسردگی دارند و حتی در شرایط عادی نیز زندگی را سخت و بی‌لذت می‌دانند."},
            "N-E+": {"name": "شاد و خوشبین (Upbeat Optimists)", "condition": "روان‌رنجوری پایین و برون‌گرایی بالا", "detailed_description": "این دسته اغلب سرزنده و بانشاط هستند و به مشکلات به عنوان چالش‌های زندگی نگاه می‌کنند. وقتی ناکام می‌شوند، ناراحت و خشمگین می‌شوند اما خیلی زود این احساسات را پشت سر می‌گذارند. آن‌ها از زندگی خود لذت می‌برند و ترجیح می‌دهند به جای گذشته روی حال و آینده خود تمرکز کنند."},
            "N+E+": {"name": "بسیار هیجانی (Strongly Emotional)", "condition": "روان‌رنجوری بالا و برون‌گرایی بالا", "detailed_description": "این افراد هم هیجان‌های منفی و هم هیجان‌های مثبت را با شدت زیادی تجربه می‌کنند و نوسان‌های خلقی دارند. روابط بین‌فردی آن‌ها ممکن است آشوبناک باشد زیرا آن‌ها به راحتی تحت تاثیر احساسات خود قرار می‌گیرند."},
            "N-E-": {"name": "کم‌هیجان (Low-keyed)", "condition": "روان‌رنجوری پایین و برون‌گرایی پایین", "detailed_description": "نه خبرهای بد و نه خبرهای خوب تاثیر زیادی روی هیجان این افراد ندارد و نسبت به اتفاقاتی که می‌تواند دیگران را شگفت‌زده یا وحشت‌زده کند، بی‌تفاوت هستند. به خاطر هیجانات محدود و سردی روانی این گروه، ممکن است روابط بین‌فردی‌‌ آن‌ها با مشکل روبه‌رو شود."}
        }},
        "defense_style": {"style_name": "سبک دفاعی (Style Of Defense)", "factors": ["neuroticism", "openness"], "axes": {"vertical": "neuroticism", "horizontal": "openness"}, "types": {
            "N+O-": {"name": "ناسازگار (Maladaptive)", "condition": "روان‌رنجوری بالا و تجربه‌پذیری پایین", "detailed_description": "کسانی که سبک دفاعی ناسازگار دارند از روش‌های غیرموثری (مثل انکار، سرکوب و جابه‌جایی) برای مقابله با مشکلات استفاده می‌کنند. آن‌ها ترجیح می‌دهند از افکار آزاردهنده و خطرهای پیش‌رو به کلی چشم‌پوشی کنند، به هیجان‌های منفی خود بی‌توجهی می‌کنند و نمی‌توانند احساسات خود را با کلمات مناسب به زبان بیاورند."},
            "N-O+": {"name": "سازگار (Adaptive)", "condition": "روان‌رنجوری پایین و تجربه‌پذیری بالا", "detailed_description": "سبک دفاعی سازگار به این معنی است که فرد از تعارض‌ها، استرس‌ها و تهدیدهای روانی درون خود آگاه است اما می‌داند چطور به شیوه‌ای خلاق و موثر با آن‌ها مقابله کند. آن‌ها ممکن است به مشکلات زندگی خود به چشم طنز نگاه کنند یا از مشکلات برای الهام‌گرفتن و خلق آثار هنری استفاده کنند."},
            "N+O+": {"name": "بیش‌حساس (Hypersensitive)", "condition": "روان‌رنجوری بالا و تجربه‌پذیری بالا", "detailed_description": "این گروه افراد در مقابل مشکلات بی‌دفاع به نظر می‌رسند. آن‌‌ها همواره گوش‌به‌زنگ هستند و بدبختی‌های احتمالی را تصور می‌کنند. ممکن است زیاد کابوس ببینند یا از جایی که تفکرات غیرعادی و خلاق دارند، از افکار عجیب خود آزرده شوند."},
            "N-O-": {"name": "غیرحساس (Unconcerned)", "condition": "روان‌رنجوری پایین و تجربه‌پذیری پایین", "detailed_description": "این دسته وضعیت‌های استرس‌زا را کم‌اهمیت می‌دانند و به ندرت هیجان‌های منفی شدید را تجربه می‌کنند. آن‌ها به تهدیدها و خطرهای احتمالی فکر نمی‌کنند بلکه روی حل مشکل یا موضوع خوشایند دیگری تمرکز می‌کنند."}
        }},
        "anger_control": {"style_name": "سبک مدیریت خشم (Style of Anger Control)", "factors": ["neuroticism", "agreeableness"], "axes": {"vertical": "neuroticism", "horizontal": "agreeableness"}, "types": {
            "N+A-": {"name": "تندخو (Temperamental)", "condition": "روان‌رنجوری بالا و سازگاری پایین", "detailed_description": "افراد تندخو با کوچک‌ترین چیزی عصبانی می‌شوند و خشم خود را مستقیم ابراز می‌کنند، حتی ممکن است تا مدت‌ها برای مسئله‌ای جزئی خشمگین بمانند. آن‌ها هنگام عصبانیت روی خودشان تمرکز می‌کنند، برای همین متوجه تاثیر رفتار خود بر دیگران نمی‌شوند و ممکن است از پرخاشگری کلامی یا فیزیکی استفاده کنند."},
            "N-A+": {"name": "آسان‌گیر (Easy-Going)", "condition": "روان‌رنجوری پایین و سازگاری بالا", "detailed_description": "افراد آسان‌گیر دیر عصبانی می‌شوند و تمایلی هم به ابراز خشم خود ندارند. اغلب ترجیح می‌دهند ببخشند و فراموش کنند یا اینکه تقصیرات را دو طرفه می‌دانند و سعی می‌کنند برای رفع اختلاف تلاش کنند."},
            "N+A+": {"name": "محجوب (Timid)", "condition": "روان‌رنجوری بالا و سازگاری بالا", "detailed_description": "افراد محجوب درباره عصبانیت با خودشان تعارض دارند. آن‌ها به‌راحتی عصبانی و غمگین می‌شوند و احساس می‌کنند قربانی شده‌اند اما چون دوست ندارند دیگران را آزار بدهند، از ابراز خشم خود صرف‌نظر می‌کنند. درنتیجه، ممکن است خشم آن‌ها علیه خودشان به درون برگردد."},
            "N-A-": {"name": "خونسرد (Cold-Blooded)", "condition": "روان‌رنجوری پایین و سازگاری پایین", "detailed_description": "این دسته افراد حتی وقتی عصبانی هستند هم ظاهر عصبانی ندارند. خشم در لحظه به آن‌ها غلبه نمی‌کند، بلکه صبر می‌کنند و خشم خود را در زمان مناسب به نحو دیگری ابراز می‌کنند تا انتقام خود را بگیرند."}
        }},
        "impulse_control": {"style_name": "سبک مدیریت تکانه (Style of Impulse Control)", "factors": ["neuroticism", "conscientiousness"], "axes": {"vertical": "neuroticism", "horizontal": "conscientiousness"}, "types": {
            "N+C-": {"name": "مهارنشده (Undercontrolled)", "condition": "روان‌رنجوری بالا و وظیفه‌شناسی پایین", "detailed_description": "این افراد اغلب تحت تاثیر تکانه‌های خود هستند و نمی‌توانند در برابر میل خود مقاومت کنند. درنتیجه، ممکن است به‌گونه‌ای عمل کنند که لذت لحظه‌ای اما آسیب بلندمدت در پیش داشته باشد. سوءمصرف مواد، افت تحصیلی، رفتارهای محاظت‌نشده جنسی از جمله خطرهایی است که آن‌ها را تهدید می‌کند."},
            "N-C+": {"name": "جهت‌مند (Directed)", "condition": "روان‌رنجوری پایین و وظیفه‌شناسی بالا", "detailed_description": "انسان‌های جهت‌مند درک روشنی از اهداف خود و راه‌های رسیدن به آن دارند. آن‌ها توانایی‌های خود را می‌شناسند و ناکامی‌ها را در صلح می‌پذیرند. همچنین،‌ می‌توانند به برنامه‌ریزی خود پایبند باشند و تکانه‌های خود را به‌خوبی مدیریت کنند."},
            "N+C+": {"name": "بیش‌ازحد مهارشده (Overcontrolled)", "condition": "روان‌رنجوری بالا و وظیفه‌شناسی بالا", "detailed_description": "این افراد رفتار خود را به‌شدت و با اضطراب زیاد مدیریت می‌کنند. آن‌ها کمال‌گرا هستند و نمی‌توانند با ناکامی‌ها کنار بیایند. اهداف آن‌ها اغلب آرمانی و دست‌نیافتنی است، درنتیجه همواره خود را برای نرسیدن به آن سرزنش می‌کنند."},
            "N-C-": {"name": "آرام (Relaxed)", "condition": "روان‌رنجوری پایین و وظیفه‌شناسی پایین", "detailed_description": "این گروه نیاز چندانی به مدیریت دقیق رفتار خود نمی‌بینند، تمایل دارند آسان‌ترین راه‌ها را انتخاب کنند و ناکامی‌های خود را با سخنرانی‌های فلسفی توجیه می‌کنند. معمولا در انجام کارهای سخت و ساختارگرا، به‌ کمک و تشویق دیگران نیاز دارند."}
        }},
        "interests": {"style_name": "سبک علایق (Style of Interests)", "factors": ["extraversion", "openness"], "axes": {"vertical": "extraversion", "horizontal": "openness"}, "types": {
            "E+O-": {"name": "مصرف‌کنندگان اصلی (Mainstream Consumers)", "condition": "برون‌گرایی بالا و تجربه‌پذیری پایین", "detailed_description": "این گروه به فعالیت‌های هنجار محبوب علاقه‌ دارند. مثل مهمانی‌ها، فعالیت‌های ورزشی، خریدن کردن، فیلم‌های پرفروش و رویدادهای اجتماعی. آن‌ها جذب مشاغلی می‌شوند که ساده هستند اما اجازه مراوده با دیگران را به آن‌ها می‌دهند. فروشندگی یکی از این شغل‌ها است."},
            "E-O+": {"name": "درون‌نگرها (Introspectors)", "condition": "برون‌گرایی پایین و تجربه‌پذیری بالا", "detailed_description": "این گروه خلاق و پر از ایده‌های نو هستند اما فعالیت‌هایی را دوست دارند که بتوانند به تنهایی انجام دهند. کتاب خواندن، نویسندگی، نقاشی، موسیقی برای آن‌ها جذابیت دارد و شغل‌هایی را ترجیح می‌دهند که هم چالش‌برانگیز باشد و هم خلوت آن‌ها را بهم نزند، مثل باستان‌شناسی یا طبیعت‌شناسی."},
            "E+O+": {"name": "تعامل‌کنندگان خلاق (Creative Interactors)", "condition": "برون‌گرایی بالا و تجربه‌پذیری بالا", "detailed_description": "این افراد به تجربه کردن چیزهای جدید و متنوع علاقه دارند و دوست دارند کشف‌های خود را با دیگران به اشتراک بگذارند. آن‌ها از سخنرانی در جمع لذت می‌برند و به خوبی می‌توانند در گروه‌ها به مباحثه بپردازند. همچنین از ملاقات با افراد مختلف و پیشینه‌ آن‌ها لذت می‌برند، درنتیجه انسان‌شناسی یا روان‌شناسی شغل مناسبی برای آن‌ها است."},
            "E-O-": {"name": "خانه‌نشین‌ها (Homebodies)", "condition": "برون‌گرایی پایین و تجربه‌پذیری پایین", "detailed_description": "خانه‌نشین‌ها به فعالیت‌هایی که بتوانند به تنهایی یا در گروه‌های کوچک انجام دهند، علاقه دارند. آن‌ها ماجراجویی و خطرپذیری را دوست ندارند اما از جمع‌آوری کلکسیون یا تماشای منظره‌ای طبیعی لذت می‌برند. مشاغلی مثل حسابداری و کتابداری برای آن‌ها مناسب است."}
        }},
        "interaction_style": {"style_name": "سبک تعامل (Style of Interactions)", "factors": ["extraversion", "agreeableness"], "axes": {"vertical": "extraversion", "horizontal": "agreeableness"}, "types": {
            "E+A-": {"name": "رهبرها (Leaders)", "condition": "برون‌گرایی بالا و سازگاری پایین", "detailed_description": "این افراد از موقعیت‌های اجتماعی به عنوان فرصتی برای درخشیدن استفاده می‌کنند. آن‌ها اعتمادبه‌نفس بالایی برای تصمیم گرفتن دارند، می‌دانند چطور دیگران را با خود همراه کنند و ترجیح می‌دهند رهبر جمع باشند."},
            "E-A+": {"name": "بی‌تکلف‌ها (The Unassuming)", "condition": "برون‌گرایی پایین و سازگاری بالا", "detailed_description": "این گروه فروتن و دلسوز هستند. آن‌ها ترجیح‌ می‌دهند تنها باشند اما با دلسوزی به نیازهای دیگران پاسخ می‌دهند. اعتماد زیاد بی‌تکلف‌ها گاهی می‌تواند باعث شود دیگران از آن‌ها سوءاستفاده کنند."},
            "E+A+": {"name": "استقبال‌کنندگان (Welcomers)", "condition": "برون‌گرایی بالا و سازگاری بالا", "detailed_description": "استقبال‌کنندگان صمیمانه از همراهی با دیگران لذت می‌برند. آن‌ها نسبت به دوستان قدیمی خود دلسبتگی زیادی دارند اما آزادانه با دوستان جدید نیز ارتباط برقرار می‌کنند. این دسته خوش‌صحبت و دلسوز هستند، درنتیجه شنونده‌های خوبی به شمار می‌آیند. همچنین صحبت کردن از ایده‌های خودشان، آن‌ها را خشنود می‌سازد."},
            "E-A-": {"name": "رقابت‌کنندگان (Competitors)", "condition": "برون‌گرایی پایین و سازگاری پایین", "detailed_description": "رقابت‌کنندگان دیگران را به عنوان دشمن بالقوه درنظر می‌گیرند و بسیار محتاط هستند، دوری و دوستی را به صمیمیت ترجیح می‌دهند و به‌شدت از حریم شخصی خود محافظت می‌کنند."}
        }},
        "activity_style": {"style_name": "سبک فعالیت (Style of Activity)", "factors": ["extraversion", "conscientiousness"], "axes": {"vertical": "extraversion", "horizontal": "conscientiousness"}, "types": {
            "E+C-": {"name": "عاشقان سرگرمی (Fun Lovers)", "condition": "برون‌گرایی بالا و وظیفه‌شناسی پایین", "detailed_description": "این افراد سرشار از انرژی و نشاط هستند اما به‌سختی می‌توانند انرژی خود را در جهتی سازنده استفاده کنند. در عوض، ترجیح می‌دهند از زندگی پرهیجان، پر از ماجراجویی و مهمانی‌های شلوغ خود لذت ببرند. آن‌ها بسیار فعال و تکانشی هستند و دنبال بهانه‌ای می‌گردند تا وظایف خود را کنار بگذارند."},
            "E-C+": {"name": "زحمت‌کش‌ها (Plodders)", "condition": "برون‌گرایی پایین و وظیفه‌شناسی بالا", "detailed_description": "این گروه کارکنانی ساختارمند هستند که بر روی کار خود تمرکز می‌کنند. آن‌ها آهسته و پیوسته وظایف خود را جلو می‌برند تا به موقع به اتمام برسند. وقت‌شناسی آن‌ها بالا است و بدون عجله و بادقت کارها را انجام می‌دهند."},
            "E+C+": {"name": "به‌دست آورندگان (Go-Getters)", "condition": "برون‌گرایی بالا و وظیفه‌شناسی بالا", "detailed_description": "به‌دست آورندگان مولد و کارآمد هستند و با سرعت بالایی کار می‌کنند. آن‌ها برای کسب مهارت‌های بیشتر مشتاقند و روش‌های توسعه‌ فردی را خودانگیخته دنبال می‌کنند."},
            "E-C-": {"name": "کم‌کارها (The Lethargic)", "condition": "برون‌گرایی پایین و وظیفه‌شناسی پایین", "detailed_description": "کم‌کارها شور و شوق زیادی از خود نشان نمی‌دهند. اهداف کمی می‌تواند در آن‌ها انگیزه ایجاد کند. آن‌ها بسیار منفعل و تکانشی رفتار می‌کنند و فقط پی رفع فوری‌ترین خواسته‌های خود هستند."}
        }},
        "attitude_style": {"style_name": "سبک نگرش (Style of Attitudes)", "factors": ["openness", "agreeableness"], "axes": {"vertical": "openness", "horizontal": "agreeableness"}, "types": {
            "O+A-": {"name": "آزاداندیشان (Free-Thinkers)", "condition": "تجربه‌پذیری بالا و سازگاری پایین", "detailed_description": "این گروه نه تحت تاثیر سنت قرار می‌گیرند و نه تحت تاثیر جریان‌های مدرن هستند، بلکه همه دیدگاه‌ها را در نظر گرفته و مورد ارزیابی قرار می‌دهند تا نگرش خاص خود را پیدا کنند. آن‌ها می‌توانند احساسات را نادیده بگیرند تا حقیقت محض را پیدا کنند."},
            "O-A+": {"name": "سنت‌گرایان (Traditionalists)", "condition": "تجربه‌پذیری پایین و سازگاری بالا", "detailed_description": "این افراد با تکیه بر سنت‌ها و آداب‌ورسوم به دنبال کشف بهترین راه زندگی هستند. از نظر آن‌ها پیروی از قوانین موجود بهترین راه برای تضمین رفاه همگی است."},
            "O+A+": {"name": "پیشرفت‌‌گرایان (Progressives)", "condition": "تجربه‌پذیری بالا و سازگاری بالا", "detailed_description": "پیشرفت‌گرایان رویکردی تحلیلی به مشکلات اجتماعی دارند و مایلند تا راه‌های جدیدی را برای حل مشکل امتحان کنند. آن‌ها به طبیعت انسان ایمان دارند و مطمئن هستند به کمک آموزش، نوآوری و همکاری می‌توان جامعه را بهبود بخشید. به‌طور کل نگاه آن‌ها عقلانی و منطقی است."},
            "O-A-": {"name": "باثبات و مصمم (Resolute)", "condition": "تجربه‌پذیری پایین و سازگاری پایین", "detailed_description": "اشخاص باثبات و مصمم، باورهای قوی و انعطاف‌ناپذیری در مورد سیاست‌های اجتماعی و اخلاق دارند. آن‌ها به فطرت انسان‌ها اعتماد ندارند و طرفدار رویکردهای سخت‌گیرانه نسبت به مشکلات اجتماعی هستند تا همگان را مجبور به رعایت قانون کنند."}
        }},
        "learning_style": {"style_name": "سبک یادگیری (Style of Learning)", "factors": ["openness", "conscientiousness"], "axes": {"vertical": "openness", "horizontal": "conscientiousness"}, "types": {
            "O+C-": {"name": "رویاپردازان (Dreamers)", "condition": "تجربه‌پذیری بالا و وظیفه‌شناسی پایین", "detailed_description": "این افراد جذب ایده‌های جدید می‌شوند و به کمک تخیل خود، ایده‌های تازه را گسترش می‌دهند. آن‌ها در شروع پروژه‌های نوآورانه خوب هستند اما در تکمیل پروژه‌ها کمتر موفق می‌شوند. رویاپردازان ابهام و عدم‌ قطعیت را به خوبی تحمل می‌کنند اما برای متمرکز ماندن، به کمک نیاز دارند."},
            "O-C+": {"name": "بخشنامه‌ای‌ها (By-the-Bookers)", "condition": "تجربه‌پذیری پایین و وظیفه‌شناسی بالا", "detailed_description": "این گروه افرادی کوشا، ساختارگرا و منظم هستند که از قوانین موجود پیروی می‌کنند. آن‌ها قدرت خیال‌پردازی بالایی ندارند و ترجیح می‌دهند از بخشنامه‌هایی که مسیر را قدم‌به‌قدم مشخص می‌کنند، استفاده کنند. یادگیری در بخشنامه‌ای‌ها قوی است اما با مسائلی که پاسخ قاطع و روشنی ندارند، مشکل دارند."},
            "O+C+": {"name": "دانش‌آموزان خوب (Good Students)", "condition": "تجربه‌پذیری بالا و وظیفه‌شناسی بالا", "detailed_description": "دانش‌آموزان خوب لزوما از دیگران باهوش‌تر نیستند اما عشق واقعی نسبت به یادگیری دارند و با سخت‌کوشی و برنامه‌ریزی پیش می‌روند. آن‌ها سطح آرمان بالایی دارند و معمولا در حل مشکلات خلاق هستند. این افراد اغلب تا جایی که بتوانند تحصیلات خود را ادامه می‌دهند."},
            "O-C-": {"name": "پژوهشگران بی‌میل (Reluctant Scholars)", "condition": "تجربه‌پذیری پایین و وظیفه‌شناسی پایین", "detailed_description": "پژوهشگران بی‌میل نسبت به فعالیت‌های علمی و فکری میل کمی دارند. درنتیجه، برای پایبند کردن‌ آن‌ها به یادگیری باید انگیزه تحصیلی آن‌ها را بالا برد. همچنین، این گروه برای حفظ تمرکز، برنامه‌ریزی و سازمان‌دهی کارهای خود به کمک نیاز دارند."}
        }},
        "character_style": {"style_name": "سبک شخصیت (Style of Character)", "factors": ["agreeableness", "conscientiousness"], "axes": {"vertical": "agreeableness", "horizontal": "conscientiousness"}, "types": {
            "A+C-": {"name": "خوش‌نیت‌ها (Well-Intentioned)", "condition": "سازگاری بالا و وظیفه‌شناسی پایین", "detailed_description": "خوش‌نیت‌ها افراد بخشنده‌ای هستند که واقعا دلسوز و نگران دیگرانند اما به‌علت بی‌برنامه بودن و پیشتکار پایین نمی‌توانند همیشه با موفقیت نیت خیر خود را دنبال کنند."},
            "A-C+": {"name": "خود-پیش‌برندگان (Self-Promoters)", "condition": "سازگاری پایین و وظیفه‌شناسی بالا", "detailed_description": "این گروه در درجه اول به نیازها، اهداف و علایق خود توجه می‌کنند. منفعت آن‌ها برای خودشان در الویت است و همین ویژگی می‌تواند سبب شود در تجارت یا سیاست افراد بسیار موفقی باشند."},
            "A+C+": {"name": "نوع‌دوستان موثر (Effective Altruists)", "condition": "سازگاری بالا و وظیفه‌شناسی بالا", "detailed_description": "این دسته نظم و استقامت بالایی دارند و به خوبی وظایف خود را تا انتها پیش می‌‌برند. از سوی دیگر، مایل به خدمت به دیگران هستند. درنتیجه، می‌توانند با پشتکار زیاد در جهت منافع جمعی کار کنند."},
            "A-C-": {"name": "نامشخص (Undistinguished)", "condition": "سازگاری پایین و وظیفه‌شناسی پایین", "detailed_description": "این افراد اراده محکمی ندارند و بیشتر به فکر راحتی و لذت خود هستند تا رفاه دیگران. آن‌ها به خاطر سازگاری و وظیفه‌شناسی پایین خود، ممکن است مشکلات رفتاری داشته باشند که باید در جهت رفع آن تلاش کنند."}
        }}
    }

    # --- Main function logic starts here ---
    try:
        if not isinstance(raw_data, dict):
            return {"status": "error", "message": "Invalid input: raw_data must be a dictionary."}

        raw_scores = {dim: 0 for dim in DIMENSIONS_META.keys()}
        for question in QUESTIONS_DATA:
            q_id = str(question["id"])
            dimension = question["dimension_id"]
            is_reverse = question["is_reverse_scored"]

            response_obj = raw_data.get(q_id)
            if not response_obj or "response" not in response_obj:
                response_value = 2
            else:
                try:
                    response_value = int(response_obj["response"])
                except (ValueError, TypeError):
                    response_value = 2

            score = (4 - response_value) if is_reverse else response_value
            raw_scores[dimension] += score

        dimensions_results = {}
        for dim_id, raw_score in raw_scores.items():
            scaled_score = round((raw_score / 48) * 100)
            strength_percentage = round((abs(50 - scaled_score) / 50) * 100)

            if raw_score <= 12: level = "کم"
            elif raw_score <= 24: level = "متوسط"
            else: level = "زیاد"

            if strength_percentage <= 33: strength_level = "ضعیف"
            elif strength_percentage <= 66: strength_level = "متوسط"
            else: strength_level = "قوی"

            dimensions_results[dim_id] = {
                "name": DIMENSIONS_META[dim_id]["name"],
                "description": DIMENSIONS_META[dim_id]["description"],
                "raw_score": {"value": raw_score, "range": [0, 48]},
                "scaled_score": {"value": scaled_score, "range": [0, 100]},
                "level": level,
                "strength_percentage": strength_percentage,
                "strength_level": strength_level,
            }

        personality_styles_results = {}
        for style_id, style_meta in PERSONALITY_STYLES_META.items():
            factors = style_meta["factors"]
            factor1_id, factor2_id = factors[0], factors[1]

            factor1_status = "+" if dimensions_results[factor1_id]["scaled_score"]["value"] >= 50 else "-"
            factor2_status = "+" if dimensions_results[factor2_id]["scaled_score"]["value"] >= 50 else "-"

            quadrant_code = f"{DIMENSIONS_META[factor1_id]['abbr']}{factor1_status}{DIMENSIONS_META[factor2_id]['abbr']}{factor2_status}"

            matching_type_data = style_meta["types"].get(quadrant_code)
            if not matching_type_data:
                matching_type = {"name": "Unknown", "condition": "Unknown", "detailed_description": "Could not determine personality style type."}
            else:
                matching_type = {
                    "name": matching_type_data["name"],
                    "quadrant_code": quadrant_code,
                    "condition": matching_type_data["condition"],
                    "detailed_description": matching_type_data["detailed_description"]
                }

            personality_styles_results[style_id] = {
                "style_name": style_meta["style_name"],
                "axes": style_meta["axes"],
                "matching_type": matching_type,
                "factor_scores": {
                    factor1_id: dimensions_results[factor1_id]["scaled_score"]["value"],
                    factor2_id: dimensions_results[factor2_id]["scaled_score"]["value"],
                },
                "factor_strength_percentages": {
                    factor1_id: dimensions_results[factor1_id]["strength_percentage"],
                    factor2_id: dimensions_results[factor2_id]["strength_percentage"],
                }
            }

        final_result = {
            "dimensions": dimensions_results,
            "personality_styles": personality_styles_results
        }

        logger.info("Successfully calculated NEO-FFI scores.")
        return final_result

    except Exception as e:
        logger.exception("An unexpected error occurred during NEO-FFI score calculation.")
        return {"status": "error", "message": str(e)}

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


def _calculate_pvq_scores(raw_data):
    """
    Calculates and interprets scores for the Schwartz Personal Values Questionnaire (PVQ).

    This function processes raw user responses to calculate scores for the ten core
    human values. It determines a grand mean from all responses to account for
    individual response bias, then calculates a centered score for each value to show
    its relative importance to the user.

    The final output is a rich JSON object designed for easy frontend consumption,
    containing a summary, a ranked list of values, and a detailed breakdown of
    scores for each value category, using ranks as keys for easy lookup.

    Args:
        raw_data (dict): The raw_results_json from a UserAssessmentAttempt.
            Expected format: {"1": {"response": "2"}, "2": {"response": "4"}, ...}

    Returns:
        dict: A dictionary containing the detailed analysis of the test,
              or an error message if the input is invalid.
    """
    # --- Self-Contained Data Structures for PVQ ---
    VALUE_CATEGORIES = {
        "self_direction": {"name_en": "Self-Direction", "name_fa": "خودرهبری", "questions": [1, 11, 22, 34]},
        "stimulation": {"name_en": "Stimulation", "name_fa": "هیجان خواهی", "questions": [6, 15, 30]},
        "hedonism": {"name_en": "Hedonism", "name_fa": "لذت جویی", "questions": [10, 26, 37]},
        "achievement": {"name_en": "Achievement", "name_fa": "موفقیت", "questions": [4, 13, 24, 32]},
        "power": {"name_en": "Power", "name_fa": "قدرت", "questions": [2, 17, 39]},
        "security": {"name_en": "Security", "name_fa": "امنیت", "questions": [5, 14, 21, 31, 35]},
        "conformity": {"name_en": "Conformity", "name_fa": "همنوایی", "questions": [7, 16, 28, 36]},
        "tradition": {"name_en": "Tradition", "name_fa": "سنت گرایی", "questions": [9, 20, 25, 38]},
        "benevolence": {"name_en": "Benevolence", "name_fa": "خیرخواهی", "questions": [12, 18, 27, 33]},
        "universalism": {"name_en": "Universalism", "name_fa": "جهان نگری", "questions": [3, 8, 19, 23, 29, 40]}
    }

    try:
        if not isinstance(raw_data, dict):
            return {"status": "error", "message": "Invalid input: raw_data must be a dictionary."}

        # --- 1. Calculate scores for each value category ---
        scores = {}
        all_responses = []
        for category_key, category_info in VALUE_CATEGORIES.items():
            total_score = 0
            category_responses = []
            for q_id in category_info["questions"]:
                q_str = str(q_id)
                if q_str in raw_data and "response" in raw_data[q_str]:
                    try:
                        score = int(raw_data[q_str]["response"])
                        total_score += score
                        category_responses.append(score)
                        all_responses.append(score)
                    except (ValueError, TypeError):
                        # Assuming complete data, but good to have a fallback.
                        # We could log a warning here if needed.
                        pass

            question_count = len(category_responses)
            avg_score = total_score / question_count if question_count > 0 else 0

            scores[category_key] = {
                "name_en": category_info["name_en"],
                "name_fa": category_info["name_fa"],
                "total_score": total_score,
                "category_average_score": round(avg_score, 2),
                "question_count": question_count,
                "responses": category_responses
            }

        # --- 2. Calculate grand mean and centered scores ---
        grand_mean = sum(all_responses) / len(all_responses) if all_responses else 0

        for category_key in scores:
            centered_score = scores[category_key]["category_average_score"] - grand_mean
            scores[category_key]["deviation_from_grand_mean"] = round(centered_score, 2)

        # --- 3. Sort by centered score to establish ranking ---
        sorted_scores_list = sorted(
            scores.items(),
            key=lambda item: item[1]["deviation_from_grand_mean"],
            reverse=True
        )

        # --- 4. Build the final output structure with ranks as keys ---
        ranking_obj = {}
        detailed_scores_obj = {}

        for idx, (category_key, data) in enumerate(sorted_scores_list):
            rank = str(idx + 1)

            # Populate the ranking object
            ranking_obj[rank] = {
                "category": category_key,
                "name_en": data["name_en"],
                "name_fa": data["name_fa"],
                "deviation_from_grand_mean": data["deviation_from_grand_mean"],
                "category_average_score": data["category_average_score"]
            }

            # Populate the detailed scores object
            detailed_scores_obj[rank] = {
                "category": category_key,
                **data # Unpack all data from the scores dict
            }

        final_result = {
            "summary": {
                "grand_mean": round(grand_mean, 2)
            },
            "ranking": ranking_obj,
            "detailed_scores": detailed_scores_obj
        }

        logger.info("Successfully calculated PVQ scores.")
        return final_result

    except Exception as e:
        logger.exception("An unexpected error occurred during PVQ score calculation.")
        return {"status": "error", "message": str(e)}


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