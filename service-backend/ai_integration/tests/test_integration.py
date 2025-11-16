# service-backend/ai_integration/tests/test_integration.py
"""
Integration tests that make actual API calls to external AI providers.
These tests verify real connectivity and response handling.

WARNING: These tests require valid API credentials and will consume API quota.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from assessment.models import TestPackage as Package, Assessment
from ai_integration.models import AIProvider, AIInteraction
from ai_integration.services import call_external_ai_provider_and_save_results, _execute_external_ai_request
import json

User = get_user_model()

# Use test AI provider configuration
MOCK_AI_PROVIDERS = {
    'ollama_cloud_test': settings.AI_PROVIDERS['ollama_cloud_test']
}


@override_settings(AI_PROVIDERS=MOCK_AI_PROVIDERS)
class AIIntegrationRealAPITests(TestCase):
    """
    Integration tests that make actual API calls to verify connectivity.
    These tests will fail if:
    - API credentials are invalid
    - API endpoint is unreachable
    - Network connectivity issues exist
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for the entire test class."""
        super().setUpClass()
        
        # Check if API key is configured
        test_config = settings.AI_PROVIDERS.get('ollama_cloud_test', {})
        cls.api_key = test_config.get('API_KEY', '')
        cls.api_url = test_config.get('URL', '')
        cls.ai_models = test_config.get('MODELS', '')
        cls.ai_model_gpt_oss_20b = cls.ai_models.get('OLLAMA_CLOUD_MODEL_gpt_oss_20b','')
        
        if not cls.api_key or not cls.api_url:
            print("\n" + "="*70)
            print("WARNING: Test API credentials not configured!")
            print("Please set the following environment variables:")
            print("  - OLLAMA_CLOUD_API_KEY_FOR_TESTING_IN_THE_AI_INTEGRATION_APP")
            print("  - OLLAMA_CLOUD_API_URL")
            print("="*70 + "\n")

    def setUp(self):
        """Set up test data for each test."""
        # Create test user
        self.user = User.objects.create_user(
            national_code='1234567890',
            phone_number='09123456789',
            password='testpass123'
        )
        
        # Create test assessment
        self.assessment = Assessment.objects.create(
            name='Test Assessment',
            json_filename='mbti',
            description='Test assessment for integration testing',
            is_active=True
        )
        
        # Create test package
        self.package = Package.objects.create(
            name='Test Package',
            price=1000,
            min_age=0,
            max_age=100,
            is_active=True,
        )
        self.package.assessments.add(self.assessment)
        
        # Create test AI provider
        self.provider = AIProvider.objects.create(
            name='Test Ollama Cloud',
            settings_config_key='ollama_cloud_test',
            is_active_for_users=True
        )

    def test_simple_api_connectivity(self):
        """
        Test 1: Simple API connectivity test with a basic prompt.
        This verifies that we can successfully connect to the AI provider.
        """
        print("\n" + "="*70)
        print("INTEGRATION TEST: Simple API Connectivity")
        print("="*70)
        
        # Skip test if credentials not configured
        if not self.api_key:
            self.skipTest("API credentials not configured. Skipping integration test.")
        
        print(f"\nTest Configuration:")
        print(f"  API URL: {self.api_url}")
        print(f"  API Key: {'*' * (len(self.api_key) - 4) + self.api_key[-4:] if len(self.api_key) > 4 else '****'}")
        
        # Prepare a simple test prompt
        test_prompt = {
            "message": "Hello! This is a test message. Please respond with 'Test successful' if you receive this, nothing more. abstraction in your response is very crucial.",
            "context": "This is an integration test for the AI service."
        }
        
        print(f"\nTest Prompt:")
        print(f"  {json.dumps(test_prompt, indent=2, ensure_ascii=False)}")
        
        try:
            print("\n→ Sending request to AI provider...")
            
            # Get the first available model from test config
            test_config = settings.AI_PROVIDERS['ollama_cloud_test']
            available_models = list(test_config.get('MODELS', {}).keys())
            
            if not available_models:
                self.fail("No models configured in test AI provider settings")
            
            # H.A. comment: 0 is deepseek v3, 1 is gpt oss 20b
            test_model = available_models[0]
            # test_model = available_models[1]
            print(f"  Using model: {test_model}")
            
            # Make actual API call
            response = _execute_external_ai_request(
                provider_key='ollama_cloud_test',
                model_key=test_model,
                prompt=test_prompt
            )
            
            print("\n✓ Request successful!")
            print(f"  HTTP Status Code: {response.status_code}")
            
            # Parse response
            response_json = response.json()
            print(f"\nFull API Response:")
            print(f"  {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            
            # Extract content based on provider format
            if 'message' in response_json and 'content' in response_json['message']:
                ai_content = response_json['message']['content']
            else:
                ai_content = str(response_json)
            
            print(f"\nExtracted AI Response Content:")
            print(f"  {ai_content}")
            
            # Assertions
            self.assertEqual(response.status_code, 200, "Expected HTTP 200 status code")
            self.assertIsNotNone(response_json, "Response should contain JSON data")
            self.assertTrue(len(ai_content) > 0, "AI response should contain content")
            
            print("\n" + "="*70)
            print("✓ INTEGRATION TEST PASSED: API connectivity verified")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n✗ Request failed with error: {e}")
            print(f"  Error type: {type(e).__name__}")
            print("\n" + "="*70)
            print("✗ INTEGRATION TEST FAILED: Could not connect to API")
            print("="*70 + "\n")
            raise

    def test_full_service_integration(self):
        """
        Test 2: Full service integration test.
        This tests the complete flow: data preparation → API call → response storage.
        """
        print("\n" + "="*70)
        print("INTEGRATION TEST: Full Service Integration")
        print("="*70)
        
        # Skip test if credentials not configured
        if not self.api_key:
            self.skipTest("API credentials not configured. Skipping integration test.")
        
        print(f"\nTest Setup:")
        print(f"  User ID: {self.user.id} (National Code: {self.user.national_code})")
        print(f"  Package ID: {self.package.id} (Name: {self.package.name})")
        print(f"  Provider: {self.provider.settings_config_key}")
        
        try:
            # Get the first available model
            test_config = settings.AI_PROVIDERS['ollama_cloud_test']
            available_models = list(test_config.get('MODELS', {}).keys())

            # H.A. comment: 0 is deepseek v3, 1 is gpt oss 20b
            test_model = available_models[0]
            # test_model = available_models[1]
            
            print(f"\n→ Calling full service function...")
            print(f"  Model: {test_model}")
            
            # Call the actual service function (no mocks!)
            interaction_id = call_external_ai_provider_and_save_results(
                user_id=self.user.id,
                package_id=self.package.id,
                provider_key='ollama_cloud_test',
                model_key=test_model
            )
            
            print(f"\n✓ Service function completed!")
            print(f"  Created AIInteraction ID: {interaction_id}")
            
            # Retrieve the saved interaction
            interaction = AIInteraction.objects.get(id=interaction_id)
            
            print(f"\n=== AIInteraction Details ===")
            print(f"  Status: {interaction.status}")
            print(f"  HTTP Status Code: {interaction.http_status_code}")
            print(f"  Timestamp sent: {interaction.timestamp_sent}")
            print(f"  Timestamp Received: {interaction.timestamp_received}")
            
            print(f"\nRequest Data:")
            print(f"  {json.dumps(interaction.full_request, indent=2, ensure_ascii=False)[:500]}...")
            
            print(f"\nFull Response:")
            print(f"  {json.dumps(interaction.full_response, indent=2, ensure_ascii=False)[:500]}...")
            
            print(f"\nProcessed Response (AI's Answer):")
            print(f"  {interaction.processed_response[:1000]}...")
            
            # Assertions
            self.assertEqual(interaction.status, AIInteraction.Status.COMPLETED, 
                           "Interaction should be marked as COMPLETED")
            self.assertEqual(interaction.http_status_code, 200,
                           "Should receive HTTP 200 status")
            self.assertIsNotNone(interaction.processed_response,
                               "Processed response should not be None")
            self.assertTrue(len(interaction.processed_response) > 0,
                          "Processed response should contain content")
            self.assertIsNotNone(interaction.full_request,
                               "Full request should be stored")
            self.assertIsNotNone(interaction.full_response,
                               "Full response should be stored")
            
            print("\n" + "="*70)
            print("✓ INTEGRATION TEST PASSED: Full service flow verified")
            print(f"  - Data preparation: ✓")
            print(f"  - API call: ✓")
            print(f"  - Response parsing: ✓")
            print(f"  - Database storage: ✓")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n✗ Service function failed with error: {e}")
            print(f"  Error type: {type(e).__name__}")
            
            # If an interaction was created, show its details
            if 'interaction' in locals():
                print(f"\n  Interaction ID: {interaction.id}")
                print(f"  Status: {interaction.status}")
                if interaction.full_response:
                    print(f"  Error response: {interaction.full_response}")
            
            print("\n" + "="*70)
            print("✗ INTEGRATION TEST FAILED: Service integration failed")
            print("="*70 + "\n")
            raise

    def test_error_handling_with_invalid_model(self):
        """
        Test 3: Error handling test with invalid model.
        This verifies that errors are properly caught and recorded.
        """
        print("\n" + "="*70)
        print("INTEGRATION TEST: Error Handling (Invalid Model)")
        print("="*70)
        
        # Skip test if credentials not configured
        if not self.api_key:
            self.skipTest("API credentials not configured. Skipping integration test.")
        
        print(f"\nTest Setup:")
        print(f"  Using invalid model name: 'non-existent-model-xyz'")
        
        try:
            print(f"\n→ Attempting API call with invalid model...")
            
            # This should fail because the model doesn't exist
            with self.assertRaises(Exception) as context:
                call_external_ai_provider_and_save_results(
                    user_id=self.user.id,
                    package_id=self.package.id,
                    provider_key='ollama_cloud_test',
                    model_key='non-existent-model-xyz'
                )
            
            print(f"\n✓ Error properly raised!")
            print(f"  Exception type: {type(context.exception).__name__}")
            print(f"  Exception message: {str(context.exception)[:200]}")
            
            # Check if interaction was created and marked as failed
            failed_interactions = AIInteraction.objects.filter(
                user=self.user,
                package=self.package,
                status=AIInteraction.Status.FAILED
            )
            
            if failed_interactions.exists():
                interaction = failed_interactions.first()
                print(f"\n✓ Failed interaction recorded in database!")
                print(f"  Interaction ID: {interaction.id}")
                print(f"  Status: {interaction.status}")
                print(f"  HTTP Status Code: {interaction.http_status_code}")
                if interaction.full_response:
                    print(f"  Error details: {str(interaction.full_response)[:200]}")
            
            print("\n" + "="*70)
            print("✓ INTEGRATION TEST PASSED: Error handling verified")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            print("\n" + "="*70)
            print("✗ INTEGRATION TEST FAILED: Unexpected error occurred")
            print("="*70 + "\n")
            raise
