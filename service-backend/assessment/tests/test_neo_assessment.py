from django.test import TestCase
import json
from assessment.services import _calculate_neo_scores

class NEOScoreCalculatorTest(TestCase):
    """
    Test suite for the _calculate_neo_scores service function.

    This suite includes tests for various scenarios to ensure the NEO-FFI
    score calculation is accurate, robust, and produces the expected
    JSON structure.
    """

    def test_with_all_max_scores(self):
        """
        Tests the calculation with all answers as "4" (کاملاً موافقم).
        This tests the upper bounds of raw scores and reverse scoring logic.
        """
        # All 60 questions answered with "4"
        raw_data = {str(i): {"response": "4"} for i in range(1, 61)}

        results = _calculate_neo_scores(raw_data)

        # 1. Check top-level structure
        self.assertIn("dimensions", results)
        self.assertIn("personality_styles", results)
        self.assertEqual(len(results["dimensions"]), 5)
        self.assertEqual(len(results["personality_styles"]), 10)

        # 2. Validate a specific dimension (Neuroticism)
        # 8 direct questions (8*4=32) + 4 reverse questions (4*0=0) = 32
        neuroticism = results["dimensions"]["neuroticism"]
        self.assertEqual(neuroticism["raw_score"]["value"], 32)
        self.assertEqual(neuroticism["scaled_score"]["value"], 67) # round((32/48)*100)
        self.assertEqual(neuroticism["level"], "زیاد")
        self.assertEqual(neuroticism["strength_percentage"], 34) # round(abs(50-67)/50*100)
        self.assertEqual(neuroticism["strength_level"], "متوسط")

        # 3. Validate a specific personality style (Well-Being)
        well_being = results["personality_styles"]["well_being"]
        self.assertEqual(well_being["matching_type"]["quadrant_code"], "N+E+")
        self.assertEqual(well_being["factor_scores"]["neuroticism"], 67)
        self.assertEqual(well_being["factor_scores"]["extraversion"], 67)


    def test_with_all_min_scores(self):
        """
        Tests the calculation with all answers as "0" (کاملاً مخالفم).
        This tests the lower bounds and reverse scoring logic.
        """
        raw_data = {str(i): {"response": "0"} for i in range(1, 61)}

        results = _calculate_neo_scores(raw_data)

        # Validate Neuroticism score: 8 direct (8*0=0) + 4 reverse (4*4=16) = 16
        neuroticism = results["dimensions"]["neuroticism"]
        self.assertEqual(neuroticism["raw_score"]["value"], 16)
        self.assertEqual(neuroticism["scaled_score"]["value"], 33) # round((16/48)*100)

        # Validate Extraversion score: 8 direct (8*0=0) + 4 reverse (4*4=16) = 16
        extraversion = results["dimensions"]["extraversion"]
        self.assertEqual(extraversion["raw_score"]["value"], 16)
        self.assertEqual(extraversion["scaled_score"]["value"], 33)


    def test_with_all_neutral_scores(self):
        """
        Tests the calculation with all answers as "2" (نظری ندارم).
        This should result in perfectly average scores across the board.
        """
        raw_data = {str(i): {"response": "2"} for i in range(1, 61)}

        results = _calculate_neo_scores(raw_data)

        for dim_id, dim_data in results["dimensions"].items():
            self.assertEqual(dim_data["raw_score"]["value"], 24)
            self.assertEqual(dim_data["scaled_score"]["value"], 50)
            self.assertEqual(dim_data["level"], "متوسط")
            self.assertEqual(dim_data["strength_percentage"], 0)

        # Check a style quadrant code
        well_being = results["personality_styles"]["well_being"]
        self.assertEqual(well_being["matching_type"]["quadrant_code"], "N+E+")


    def test_realistic_scenario(self):
        """
        Tests with a more realistic, mixed set of answers to check
        the logic under normal conditions.
        """
        raw_data = {
            "1": {"response": "1"}, "2": {"response": "3"}, "3": {"response": "4"}, "4": {"response": "0"}, "5": {"response": "1"},
            "6": {"response": "3"}, "7": {"response": "2"}, "8": {"response": "1"}, "9": {"response": "0"}, "10": {"response": "4"},
            "11": {"response": "4"}, "12": {"response": "3"}, "13": {"response": "2"}, "14": {"response": "1"}, "15": {"response": "0"},
            "16": {"response": "1"}, "17": {"response": "2"}, "18": {"response": "3"}, "19": {"response": "4"}, "20": {"response": "0"},
            "21": {"response": "1"}, "22": {"response": "2"}, "23": {"response": "3"}, "24": {"response": "4"}, "25": {"response": "0"},
            "26": {"response": "1"}, "27": {"response": "2"}, "28": {"response": "3"}, "29": {"response": "4"}, "30": {"response": "0"},
            "31": {"response": "1"}, "32": {"response": "2"}, "33": {"response": "3"}, "34": {"response": "4"}, "35": {"response": "0"},
            "36": {"response": "1"}, "37": {"response": "2"}, "38": {"response": "3"}, "39": {"response": "4"}, "40": {"response": "0"},
            "41": {"response": "1"}, "42": {"response": "2"}, "43": {"response": "3"}, "44": {"response": "4"}, "45": {"response": "0"},
            "46": {"response": "1"}, "47": {"response": "2"}, "48": {"response": "3"}, "49": {"response": "4"}, "50": {"response": "0"},
            "51": {"response": "1"}, "52": {"response": "2"}, "53": {"response": "3"}, "54": {"response": "4"}, "55": {"response": "0"},
            "56": {"response": "1"}, "57": {"response": "2"}, "58": {"response": "3"}, "59": {"response": "4"}, "60": {"response": "0"}
        }

        results = _calculate_neo_scores(raw_data)

        # Check a few values to ensure calculation is proceeding as expected
        neuroticism = results["dimensions"]["neuroticism"]
        self.assertEqual(neuroticism["raw_score"]["value"], 25)
        self.assertEqual(neuroticism["scaled_score"]["value"], 52)

        openness = results["dimensions"]["openness"]
        self.assertEqual(openness["raw_score"]["value"], 22)
        self.assertEqual(openness["scaled_score"]["value"], 46)
        self.assertEqual(openness["level"], "متوسط")
        self.assertEqual(openness["strength_percentage"], 8)
        self.assertEqual(openness["strength_level"], "ضعیف")

        # Check a resulting personality style
        defense_style = results["personality_styles"]["defense_style"]
        self.assertEqual(defense_style["matching_type"]["quadrant_code"], "N+O-")
        self.assertEqual(defense_style["matching_type"]["name"], "ناسازگار (Maladaptive)")