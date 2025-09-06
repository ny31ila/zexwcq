# project_root/service-backend/core/celery.py
"""
Celery configuration for the core project.

This module defines the Celery application instance and configures it
to use Django's settings. It's automatically discovered by Celery
when the Django project is loaded.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create the Celery application instance.
app = Celery('core')

# Configure Celery to use the Django settings.
# This looks for CELERY_* settings in your Django settings.py.
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
# This automatically discovers tasks.py files in your Django apps.
app.autodiscover_tasks()

# Optional: Define a test task
# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
