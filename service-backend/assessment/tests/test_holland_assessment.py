# service-backend/assessment/tests/test_holland_assessment.py
from django.test import TestCase
from assessment.services import _calculate_holland_scores

class HollandScoreCalculatorTest(TestCase):

    def test_holland_1(self):
        """
        Test case with a clear 'RIA' profile.
        """
        raw_data = {
            "interests_____artistic_____3": {"response": True},
            "self_assessment_1_____3": {"response": "5"},
            "interests_____investigative_____2": {"response": True},
            "self_assessment_1_____2": {"response": "4"},
            "interests_____realistic_____1": {"response": True},
            "self_assessment_1_____1": {"response": "3"},
        }

        result = _calculate_holland_scores(raw_data)
        self.assertEqual(result['holland_code'], 'A-I-R')

    def test_holland_2(self):
        """
        Test case where all scores are equal.
        """
        raw_data = {
            "interests_____realistic_____1": {"response": True},
            "interests_____investigative_____2": {"response": True},
            "interests_____artistic_____3": {"response": True},
            "interests_____social_____4": {"response": True},
            "interests_____enterprising_____5": {"response": True},
            "interests_____conventional_____6": {"response": True},
        }

        result = _calculate_holland_scores(raw_data)
        self.assertEqual(result['holland_code'], 'A/C/E/I/R/S')

    def test_holland_3(self):
        """
        Test case with a clear 'SEC' profile.
        """
        raw_data = {
            "interests_____conventional_____6": {"response": True},
            "self_assessment_1_____6": {"response": "5"},
            "interests_____enterprising_____5": {"response": True},
            "self_assessment_1_____5": {"response": "4"},
            "interests_____social_____4": {"response": True},
            "self_assessment_1_____4": {"response": "3"},
        }

        result = _calculate_holland_scores(raw_data)
        self.assertEqual(result['holland_code'], 'C-E-S')
