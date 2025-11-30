# service-backend/assessment/tests/test_mbti_assessment.py
from django.test import TestCase
from assessment.services import _calculate_mbti_scores

class MBTIScoreCalculatorTest(TestCase):

    def test_mbti_1(self):
        """
        Test case for a clear ISTJ profile.
        """
        raw_data = {str(i): {"response": "a"} for i in range(1, 61)}

        result = _calculate_mbti_scores(raw_data)
        self.assertEqual(result['mbti_type'], 'ISTP')

    def test_mbti_2(self):
        """
        Test case for a clear ENFP profile.
        """
        raw_data = {str(i): {"response": "b"} for i in range(1, 61)}

        result = _calculate_mbti_scores(raw_data)
        self.assertEqual(result['mbti_type'], 'ENFJ')

    def test_mbti_3_near_tie(self):
        """
        Test case with a near tie in the E/I dimension.
        """
        raw_data = {
            "1": {"response": "a"}, "5": {"response": "a"}, "9": {"response": "a"}, "13": {"response": "a"},
            "17": {"response": "a"}, "21": {"response": "a"}, "25": {"response": "a"},
            "29": {"response": "b"}, "33": {"response": "b"}, "37": {"response": "b"}, "41": {"response": "b"},
            "45": {"response": "b"}, "49": {"response": "b"}, "53": {"response": "b"}, "57": {"response": "b"},
        }

        result = _calculate_mbti_scores(raw_data)
        self.assertEqual(result['scores']['I'], 7)
        self.assertEqual(result['scores']['E'], 8)
        self.assertEqual(result['preferences']['EI']['preference'], 'E')
