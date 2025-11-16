# service-backend/ai_integration/services.py
"""
Service functions for orchestrating interactions with external AI providers.
"""
import logging
import json
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import AIInteraction, AIProvider
from assessment.services import prepare_aggregated_package_data_for_ai
from account.models import User
from assessment.models import TestPackage as Package

logger = logging.getLogger(__name__)

def _parse_successful_response(provider_key: str, response_data: dict) -> str:
    """
    Parses the successful JSON response from an AI provider to extract the clean,
    user-facing text content.
    """
    if provider_key == 'ollama_cloud':
        try:
            return response_data['message']['content']
        except (KeyError, TypeError) as e:
            logger.error(f"Could not parse successful response from {provider_key}: {e}. Response data: {response_data}")
            return "Error: Could not parse AI response."
    # Add elif blocks here for other providers in the future
    else:
        logger.warning(f"No response parsing logic defined for provider '{provider_key}'. Returning raw JSON.")
        return json.dumps(response_data)

def _execute_external_ai_request(provider_key: str, model_key: str, prompt: dict) -> requests.Response:
    """
    Builds and executes the HTTP request to the specified AI provider.
    Handles dynamic insertion of keys, models, and prompts into templates.
    """
    provider_config = settings.AI_PROVIDERS[provider_key]
    api_key = provider_config.get('API_KEY', '')

    # Build headers
    headers = {k: v.format(api_key=api_key) for k, v in provider_config['HEADERS'].items()}

    # Build payload
    payload = provider_config['PAYLOAD_TEMPLATE'].copy()
    payload['model'] = model_key
    # This assumes the prompt is always placed in the 'messages' list.
    # This might need to be made more flexible for other providers.
    for message in payload.get('messages', []):
        if message.get('content') == '{prompt}':
            message['content'] = json.dumps(prompt, ensure_ascii=False)

    logger.info(f"Sending request to {provider_config['URL']} with model {model_key}.")

    response = requests.post(
        provider_config['URL'],
        headers=headers,
        json=payload,
        timeout=120  # Set a generous timeout
    )
    response.raise_for_status()  # Will raise HTTPError for 4xx/5xx responses
    return response

@transaction.atomic
def call_external_ai_provider_and_save_results(
    user_id: int,
    package_id: int,
    provider_key: str,
    model_key: str
):
    """
    Orchestrates the entire process of sending a request to an AI provider and
    recording the interaction in the database.
    """
    try:
        user = User.objects.get(pk=user_id)
        package = Package.objects.get(pk=package_id)
        provider = AIProvider.objects.get(settings_config_key=provider_key)

        # 1. Prepare the data and prompt (pass model instances, not IDs)
        aggregated_data = prepare_aggregated_package_data_for_ai(user, package)

        # 2. Create the initial AIInteraction record
        interaction = AIInteraction.objects.create(
            user=user,
            package=package,
            provider=provider,
            status=AIInteraction.Status.PENDING,
            full_request=aggregated_data # Store the prompt data as the request
        )
        logger.info(f"Created pending AIInteraction (ID: {interaction.id}) for user {user_id}, package {package_id}.")

        # 3. Execute the external API call
        response = _execute_external_ai_request(provider_key, model_key, aggregated_data)

        # 4. Process the successful response
        interaction.http_status_code = response.status_code
        interaction.timestamp_received = timezone.now()

        try:
            response_json = response.json()
            interaction.full_response = response_json
            interaction.processed_response = _parse_successful_response(provider_key, response_json)
            interaction.status = AIInteraction.Status.COMPLETED
            logger.info(f"AIInteraction (ID: {interaction.id}) completed successfully.")
        except json.JSONDecodeError:
            interaction.full_response = {'error': 'Response was not valid JSON.', 'content': response.text}
            interaction.processed_response = "Error: The response from the AI provider was not valid JSON."
            interaction.status = AIInteraction.Status.FAILED
            logger.error(f"AIInteraction (ID: {interaction.id}) failed: Invalid JSON response.")

    except (User.DoesNotExist, Package.DoesNotExist, AIProvider.DoesNotExist) as e:
        logger.error(f"Could not initiate AI call. Invalid reference: {e}")
        # No interaction object to update, so we just log and exit.
        raise

    except requests.exceptions.RequestException as e:
        logger.error(f"AI request failed for interaction (ID: {interaction.id}). Error: {e}")
        if 'interaction' in locals():
            interaction.status = AIInteraction.Status.FAILED
            if e.response is not None:
                interaction.http_status_code = e.response.status_code
                try:
                    interaction.full_response = e.response.json()
                except json.JSONDecodeError:
                    interaction.full_response = {'error': 'Failed to decode error response as JSON.', 'content': e.response.text}
            interaction.timestamp_received = timezone.now()
        # Re-raise the exception to allow Celery to handle retries
        raise

    except Exception as e:
        # Avoid referencing 'interaction' if it wasn't created yet
        if 'interaction' in locals():
            logger.critical(
                f"An unexpected error occurred for interaction (ID: {interaction.id}). Error: {e}",
                exc_info=True
            )
            interaction.status = AIInteraction.Status.FAILED
            interaction.full_response = {'error': 'An unexpected critical error occurred.', 'details': str(e)}
            interaction.timestamp_received = timezone.now()
        else:
            logger.critical(
                f"An unexpected error occurred before interaction creation. Error: {e}",
                exc_info=True
            )
        raise

    finally:
        if 'interaction' in locals():
            interaction.save()
            logger.info(f"Saved final state for AIInteraction (ID: {interaction.id}) with status '{interaction.status}'.")

    return interaction.id
