# service-backend/assessment/tests/test_services.py

from django.test import TestCase
from assessment.services import _calculate_swanson_scores

class SwansonAssessmentScoringTest(TestCase):
    def test_calculate_swanson_scores_predominantly_inattentive(self):
        """
        Test case where the user's responses indicate a "Predominantly Inattentive" result.
        Inattention score is high, hyperactivity is low.
        """
        raw_data = {
            "1": {"response": "3"}, "2": {"response": "3"}, "3": {"response": "2"},
            "4": {"response": "2"}, "5": {"response": "1"}, "6": {"response": "1"},
            "7": {"response": "2"}, "8": {"response": "3"}, "9": {"response": "2"},
            "10": {"response": "0"}, "11": {"response": "1"}, "12": {"response": "0"},
            "13": {"response": "1"}, "14": {"response": "0"}, "15": {"response": "1"},
            "16": {"response": "0"}, "17": {"response": "1"}, "18": {"response": "0"}
        }

        result = _calculate_swanson_scores(raw_data)

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['scores']['inattention']['sum'], 19)
        self.assertAlmostEqual(result['scores']['inattention']['average'], 2.11)
        self.assertEqual(result['scores']['hyperactivity_impulsivity']['sum'], 4)
        self.assertAlmostEqual(result['scores']['hyperactivity_impulsivity']['average'], 0.44)

        self.assertEqual(result['interpretation']['category']['id'], 'Predominantly Inattentive')
        self.assertEqual(result['interpretation']['subscale_status']['inattention']['status'], 'Above cutoff')
        self.assertEqual(result['interpretation']['subscale_status']['hyperactivity_impulsivity']['status'], 'Below cutoff')

    def test_calculate_swanson_scores_combined(self):
        """
        Test case for a "Combined" result where both scores are high.
        """
        raw_data = {
            "1": {"response": "3"}, "2": {"response": "2"}, "3": {"response": "3"},
            "4": {"response": "2"}, "5": {"response": "2"}, "6": {"response": "3"},
            "7": {"response": "2"}, "8": {"response": "3"}, "9": {"response": "2"},
            "10": {"response": "3"}, "11": {"response": "2"}, "12": {"response": "3"},
            "13": {"response": "2"}, "14": {"response": "3"}, "15": {"response": "2"},
            "16": {"response": "3"}, "17": {"response": "2"}, "18": {"response": "3"}
        }

        result = _calculate_swanson_scores(raw_data)

        self.assertEqual(result['scores']['inattention']['sum'], 22)
        self.assertAlmostEqual(result['scores']['inattention']['average'], 2.44)
        self.assertEqual(result['scores']['hyperactivity_impulsivity']['sum'], 23)
        self.assertAlmostEqual(result['scores']['hyperactivity_impulsivity']['average'], 2.56)

        self.assertEqual(result['interpretation']['category']['id'], 'Combined')
        self.assertEqual(result['interpretation']['subscale_status']['inattention']['status'], 'Above cutoff')
        self.assertEqual(result['interpretation']['subscale_status']['hyperactivity_impulsivity']['status'], 'Above cutoff')

    def test_calculate_swanson_scores_no_significant_adhd(self):
        """
        Test case for "No Significant ADHD" where all scores are low.
        """
        raw_data = {
            "1": {"response": "0"}, "2": {"response": "0"}, "3": {"response": "1"},
            "4": {"response": "0"}, "5": {"response": "0"}, "6": {"response": "1"},
            "7": {"response": "0"}, "8": {"response": "0"}, "9": {"response": "1"},
            "10": {"response": "0"}, "11": {"response": "1"}, "12": {"response": "0"},
            "13": {"response": "0"}, "14": {"response": "1"}, "15": {"response": "0"},
            "16": {"response": "0"}, "17": {"response": "1"}, "18": {"response": "0"}
        }

        result = _calculate_swanson_scores(raw_data)

        self.assertEqual(result['scores']['inattention']['sum'], 3)
        self.assertAlmostEqual(result['scores']['inattention']['average'], 0.33)
        self.assertEqual(result['scores']['hyperactivity_impulsivity']['sum'], 3)
        self.assertAlmostEqual(result['scores']['hyperactivity_impulsivity']['average'], 0.33)

        self.assertEqual(result['interpretation']['category']['id'], 'No Significant ADHD')
        self.assertEqual(result['interpretation']['subscale_status']['inattention']['status'], 'Below cutoff')
        self.assertEqual(result['interpretation']['subscale_status']['hyperactivity_impulsivity']['status'], 'Below cutoff')
