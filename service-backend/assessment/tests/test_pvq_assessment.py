# service-backend/assessment/tests/test_pvq_assessment.py
from django.test import TestCase
from assessment.services import _calculate_pvq_scores

class PVQScoreCalculatorTest(TestCase):

    def test_pvq_1(self):
        """
        Test case with a clear self-direction and stimulation profile.
        """
        raw_data = {
            "1": {"response": "6"}, "11": {"response": "6"}, "22": {"response": "6"}, "34": {"response": "6"},
            "6": {"response": "6"}, "15": {"response": "6"}, "30": {"response": "6"},
        }

        result = _calculate_pvq_scores(raw_data)
        self.assertEqual(result['ranking']['1']['category'], 'self_direction')
        self.assertEqual(result['ranking']['2']['category'], 'stimulation')

    def test_pvq_2(self):
        """
        Test case where all scores are equal.
        """
        raw_data = {str(i): {"response": "3"} for i in range(1, 41)}

        result = _calculate_pvq_scores(raw_data)
        self.assertEqual(result['summary']['grand_mean'], 3.0)

    def test_pvq_3(self):
        """
        Test case with a clear power and achievement profile.
        """
        raw_data = {
            # Power questions (3 questions)
            "2": {"response": "6"}, "17": {"response": "6"}, "39": {"response": "6"},
            # Achievement questions (4 questions) - give a slightly lower score to ensure power is ranked higher
            "4": {"response": "5"}, "13": {"response": "5"}, "24": {"response": "5"}, "32": {"response": "5"},
        }

        result = _calculate_pvq_scores(raw_data)
        self.assertEqual(result['ranking']['1']['category'], 'power')
        self.assertEqual(result['ranking']['2']['category'], 'achievement')
