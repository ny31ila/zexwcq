# service-backend/ai_integration/tests/test_services.py
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.core.exceptions import ObjectDoesNotExist
from assessment.models import TestPackage as Package, Assessment
from ai_integration.models import AIProvider, AIInteraction
from ai_integration.services import call_external_ai_provider_and_save_results
import requests
from django.conf import settings

User = get_user_model()

MOCK_AI_PROVIDERS = {
    'ollama_cloud': settings.AI_PROVIDERS['ollama_cloud_test']
}

@override_settings(AI_PROVIDERS=MOCK_AI_PROVIDERS)
class AIIntegrationServiceTests(TestCase):

    def setUp(self):
        """Set up non-database objects for testing."""
        self.user_instance = MagicMock(spec=User, id=1)
        self.package_instance = MagicMock(spec=Package, id=1)
        self.provider_instance = MagicMock(spec=AIProvider, id=1)

    @patch('ai_integration.services.AIProvider')
    @patch('ai_integration.services.Package')
    @patch('ai_integration.services.User')
    @patch('ai_integration.models.AIInteraction.objects.create')
    @patch('ai_integration.services._execute_external_ai_request')
    @patch('ai_integration.services.prepare_aggregated_package_data_for_ai')
    def test_call_external_ai_provider_success(
        self, mock_prepare_data, mock_execute_request, mock_interaction_create,
        mock_user_model, mock_package_model, mock_provider_model):
        """
        Test the successful execution of the service function using mocks.
        """
        # --- Mock setup ---
        mock_prepare_data.return_value = {"user_data": {}}
        # Configure mocks to return instances and have a valid DoesNotExist exception
        mock_user_model.objects.get.return_value = self.user_instance
        mock_user_model.DoesNotExist = ObjectDoesNotExist
        mock_package_model.objects.get.return_value = self.package_instance
        mock_package_model.DoesNotExist = ObjectDoesNotExist
        mock_provider_model.objects.get.return_value = self.provider_instance
        mock_provider_model.DoesNotExist = ObjectDoesNotExist

        mock_interaction = MagicMock(spec=AIInteraction)
        mock_interaction_create.return_value = mock_interaction

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "Success!"}}
        mock_execute_request.return_value = mock_response

        # --- Execute ---
        call_external_ai_provider_and_save_results(
            user_id=1, package_id=1, provider_key='ollama_cloud', model_key='test_model'
        )

        # --- Assertions ---
        mock_interaction_create.assert_called_once_with(
            user=self.user_instance, package=self.package_instance, provider=self.provider_instance,
            status=AIInteraction.Status.PENDING, full_request={"user_data": {}}
        )
        self.assertEqual(mock_interaction.status, AIInteraction.Status.COMPLETED)
        self.assertEqual(mock_interaction.http_status_code, 200)
        self.assertEqual(mock_interaction.processed_response, "Success!")
        mock_interaction.save.assert_called_once()

    @patch('ai_integration.services.AIProvider')
    @patch('ai_integration.services.Package')
    @patch('ai_integration.services.User')
    @patch('ai_integration.models.AIInteraction.objects.create')
    @patch('ai_integration.services._execute_external_ai_request')
    @patch('ai_integration.services.prepare_aggregated_package_data_for_ai')
    def test_call_external_ai_provider_http_error(
        self, mock_prepare_data, mock_execute_request, mock_interaction_create,
        mock_user_model, mock_package_model, mock_provider_model):
        """
        Test that the interaction object is correctly updated to 'failed' on an HTTP error.
        """
        # --- Mock setup ---
        mock_prepare_data.return_value = {"user_data": {}}
        mock_user_model.objects.get.return_value = self.user_instance
        mock_user_model.DoesNotExist = ObjectDoesNotExist
        mock_package_model.objects.get.return_value = self.package_instance
        mock_package_model.DoesNotExist = ObjectDoesNotExist
        mock_provider_model.objects.get.return_value = self.provider_instance
        mock_provider_model.DoesNotExist = ObjectDoesNotExist

        mock_interaction = MagicMock(spec=AIInteraction)
        mock_interaction_create.return_value = mock_interaction

        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock(status_code=401, json=lambda: {"error": "Invalid API key"})
        mock_execute_request.side_effect = http_error

        # --- Execute and assert exception ---
        with self.assertRaises(requests.exceptions.HTTPError):
            call_external_ai_provider_and_save_results(
                user_id=1, package_id=1, provider_key='ollama_cloud', model_key='test_model'
            )

        # --- Assertions on the mocked object ---
        self.assertEqual(mock_interaction.status, AIInteraction.Status.FAILED)
        self.assertEqual(mock_interaction.http_status_code, 401)
        self.assertEqual(mock_interaction.full_response, {"error": "Invalid API key"})
        mock_interaction.save.assert_called_once()
