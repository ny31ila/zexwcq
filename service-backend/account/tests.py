# service-backend/account/tests.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountTests(APITestCase):
    """
    Test suite for the account app.
    """

    def test_user_registration_success(self):
        """
        Ensure a new user can be created successfully.
        """
        url = reverse('account:user_register')
        data = {
            "national_code": "1234567890",
            "phone_number": "09123456789",
            "password": "a-very-strong-password-123!",
            "password_confirm": "a-very-strong-password-123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(national_code="1234567890").exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().first_name, 'Test')

    def test_user_registration_password_mismatch(self):
        """
        Ensure registration fails when passwords do not match.
        """
        url = reverse('account:user_register')
        data = {
            "national_code": "1234567891",
            "phone_number": "09123456780",
            "password": "a-very-strong-password-123!",
            "password_confirm": "a-different-password-456!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
        self.assertFalse(User.objects.filter(national_code="1234567891").exists())
