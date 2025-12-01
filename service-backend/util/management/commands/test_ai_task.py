# service-backend/util/management/commands/test_ai_task.py
"""
Management command to trigger a test Celery task.
This is used to verify the Celery/Redis setup.
"""

from django.core.management.base import BaseCommand
from ai_integration.tasks import test_celery_connection

class Command(BaseCommand):
    help = 'Triggers a test Celery task to verify the connection.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--message',
            type=str,
            default="Hello, Celery!",
            help='A simple message to send to the test task.'
        )

    def handle(self, *args, **options):
        message = options['message']
        self.stdout.write(
            self.style.NOTICE(f"Triggering test Celery task with message: '{message}'")
        )

        # Trigger the Celery task asynchronously
        task_result = test_celery_connection.delay(message)

        self.stdout.write(
            self.style.SUCCESS(
                f'Test task triggered successfully. Task ID: {task_result.id}'
            )
        )
        self.stdout.write(
            "Use 'docker compose logs -f service-celery' to monitor the task execution."
        )
