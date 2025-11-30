# service-backend/assessment/tests/test_gardner_assessment.py
from django.test import TestCase
from assessment.services import _calculate_gardner_scores

class GardnerScoreCalculatorTest(TestCase):

    def test_gardner_1(self):
        """
        Test case with a clear linguistic-verbal and logical-mathematical profile.
        """
        raw_data = {}
        # Max scores for linguistic_verbal (questions 1, 9, 17, ...) and logical_mathematical (2, 10, 18, ...)
        for i in range(1, 81):
            if (i % 8 == 1) or (i % 8 == 2):
                raw_data[str(i)] = {"response": "5"}
            else:
                raw_data[str(i)] = {"response": "1"}

        result = _calculate_gardner_scores(raw_data)
        self.assertEqual(result['ranked_intelligences'][0]['dimension_id'], 'linguistic_verbal')
        self.assertEqual(result['ranked_intelligences'][1]['dimension_id'], 'logical_mathematical')

    def test_gardner_2(self):
        """
        Test case where all scores are equal.
        """
        raw_data = {str(i): {"response": "3"} for i in range(1, 81)}

        result = _calculate_gardner_scores(raw_data)
        self.assertEqual(result['total_interpretation'], 'هوش چندگانه فرد متوسط است.')

    def test_gardner_3(self):
        """
        Test case with a clear naturalist and musical profile.
        """
        raw_data = {}
        # Max scores for naturalist (questions 8, 16, 24, ...) and high scores for musical (7, 15, 23, ...)
        for i in range(1, 81):
            if i % 8 == 0:
                raw_data[str(i)] = {"response": "5"}
            elif i % 8 == 7:
                raw_data[str(i)] = {"response": "4"}
            else:
                raw_data[str(i)] = {"response": "1"}

        result = _calculate_gardner_scores(raw_data)
        self.assertEqual(result['ranked_intelligences'][0]['dimension_id'], 'naturalist')
        self.assertEqual(result['ranked_intelligences'][1]['dimension_id'], 'musical')
