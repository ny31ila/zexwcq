# service-backend/core/management/commands/test_ai_task.py
"""
Management command to trigger the test OpenRouter Celery task.
This is used to verify the Celery/Redis setup.
"""

from django.core.management.base import BaseCommand
from ai_integration.tasks import test_openrouter_task

class Command(BaseCommand):
    help = 'Triggers the test OpenRouter Celery task to verify setup.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prompt',
            type=str,
            default="What is 2+2? Explain the calculation in Python.",
            help='The prompt text to send to the OpenRouter API (default: a simple math question)'
        )

    def handle(self, *args, **options):
        prompt_text = options['prompt']
        self.stdout.write(
            self.style.NOTICE(f'Triggering test OpenRouter task with prompt: "{prompt_text}"')
        )
        
        # Trigger the Celery task asynchronously
        task_result = test_openrouter_task.delay(prompt_text)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test task triggered successfully. Task ID: {task_result.id}'
            )
        )
        self.stdout.write(
            "Use 'docker-compose logs service-celery' to monitor the task execution."
        )
