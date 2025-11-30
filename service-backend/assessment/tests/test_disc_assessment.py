# service-backend/assessment/tests/test_disc_assessment.py
from django.test import TestCase
from assessment.services import _calculate_disc_scores

class DISCScoreCalculatorTest(TestCase):

    def test_disc_1(self):
        """
        Test case with a clear 'D' profile.
        """
        raw_data = {
            "1": {"most_like_me": "D", "least_like_me": "I"}, "2": {"most_like_me": "D", "least_like_me": "S"},
            "3": {"most_like_me": "D", "least_like_me": "C"}, "4": {"most_like_me": "D", "least_like_me": "I"},
            "5": {"most_like_me": "D", "least_like_me": "S"}, "6": {"most_like_me": "D", "least_like_me": "C"},
            "7": {"most_like_me": "D", "least_like_me": "I"}, "8": {"most_like_me": "D", "least_like_me": "S"},
            "9": {"most_like_me": "D", "least_like_me": "C"}, "10": {"most_like_me": "D", "least_like_me": "I"},
            "11": {"most_like_me": "D", "least_like_me": "S"}, "12": {"most_like_me": "D", "least_like_me": "C"},
            "13": {"most_like_me": "I", "least_like_me": "D"}, "14": {"most_like_me": "S", "least_like_me": "D"},
            "15": {"most_like_me": "C", "least_like_me": "D"}, "16": {"most_like_me": "I", "least_like_me": "D"},
            "17": {"most_like_me": "S", "least_like_me": "D"}, "18": {"most_like_me": "C", "least_like_me": "D"},
            "19": {"most_like_me": "I", "least_like_me": "S"}, "20": {"most_like_me": "S", "least_like_me": "C"},
            "21": {"most_like_me": "C", "least_like_me": "I"}, "22": {"most_like_me": "I", "least_like_me": "S"},
            "23": {"most_like_me": "S", "least_like_me": "C"}, "24": {"most_like_me": "C", "least_like_me": "I"}
        }

        result = _calculate_disc_scores(raw_data)
        self.assertEqual(result['final_behavioral_pattern']['id'], 'D')

    def test_disc_2(self):
        """
        Test case with a clear 'IS' profile.
        """
        # This data is crafted to make 'I' and 'S' the highest perceived scores.
        # Most Like: I=8, S=8, D=4, C=4
        # Least Like: I=4, S=4, D=8, C=8
        # Perceived: I=4, S=4, D=-4, C=-4
        # This will result in a clear 'IS' profile.
        raw_data = {
            "1": {"most_like_me": "I", "least_like_me": "D"}, "2": {"most_like_me": "I", "least_like_me": "D"},
            "3": {"most_like_me": "I", "least_like_me": "D"}, "4": {"most_like_me": "I", "least_like_me": "D"},
            "5": {"most_like_me": "I", "least_like_me": "C"}, "6": {"most_like_me": "I", "least_like_me": "C"},
            "7": {"most_like_me": "I", "least_like_me": "C"}, "8": {"most_like_me": "I", "least_like_me": "C"},
            "9": {"most_like_me": "S", "least_like_me": "D"}, "10": {"most_like_me": "S", "least_like_me": "D"},
            "11": {"most_like_me": "S", "least_like_me": "D"}, "12": {"most_like_me": "S", "least_like_me": "D"},
            "13": {"most_like_me": "S", "least_like_me": "C"}, "14": {"most_like_me": "S", "least_like_me": "C"},
            "15": {"most_like_me": "S", "least_like_me": "C"}, "16": {"most_like_me": "S", "least_like_me": "C"},
            "17": {"most_like_me": "D", "least_like_me": "I"}, "18": {"most_like_me": "D", "least_like_me": "I"},
            "19": {"most_like_me": "D", "least_like_me": "S"}, "20": {"most_like_me": "D", "least_like_me": "S"},
            "21": {"most_like_me": "C", "least_like_me": "I"}, "22": {"most_like_me": "C", "least_like_me": "I"},
            "23": {"most_like_me": "C", "least_like_me": "S"}, "24": {"most_like_me": "C", "least_like_me": "S"}
        }

        result = _calculate_disc_scores(raw_data)
        self.assertEqual(result['final_behavioral_pattern']['id'], 'IS')

    def test_disc_3(self):
        """
        Test case where stress level is high.
        """
        raw_data = {
            "1": {"most_like_me": "D", "least_like_me": "C"},
            "2": {"most_like_me": "D", "least_like_me": "C"},
            "3": {"most_like_me": "D", "least_like_me": "C"},
            "4": {"most_like_me": "D", "least_like_me": "C"},
            "5": {"most_like_me": "D", "least_like_me": "C"},
            "6": {"most_like_me": "D", "least_like_me": "C"},
            "7": {"most_like_me": "D", "least_like_me": "C"},
            "8": {"most_like_me": "D", "least_like_me": "C"},
            "9": {"most_like_me": "D", "least_like_me": "C"},
            "10": {"most_like_me": "D", "least_like_me": "C"},
            "11": {"most_like_me": "D", "least_like_me": "C"},
            "12": {"most_like_me": "D", "least_like_me": "C"},
            "13": {"most_like_me": "I", "least_like_me": "S"},
            "14": {"most_like_me": "I", "least_like_me": "S"},
            "15": {"most_like_me": "I", "least_like_me": "S"},
            "16": {"most_like_me": "I", "least_like_me": "S"},
            "17": {"most_like_me": "I", "least_like_me": "S"},
            "18": {"most_like_me": "I", "least_like_me": "S"},
            "19": {"most_like_me": "I", "least_like_me": "S"},
            "20": {"most_like_me": "I", "least_like_me": "S"},
            "21": {"most_like_me": "I", "least_like_me": "S"},
            "22": {"most_like_me": "I", "least_like_me": "S"},
            "23": {"most_like_me": "I", "least_like_me": "S"},
            "24": {"most_like_me": "I", "least_like_me": "S"}
        }

        result = _calculate_disc_scores(raw_data)
        self.assertEqual(result['stress_analysis']['level'], 'زیاد')
