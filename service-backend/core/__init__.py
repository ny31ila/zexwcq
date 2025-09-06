# project_root/service-backend/core/__init__.py
"""
Core project package initialization.

This file ensures that the Celery app is properly initialized
when Django starts.
"""

# Import the Celery app instance.
# This is crucial for Celery to work with Django.
from .celery import app as celery_app

# Make the Celery app available at the package level.
# This ensures it's loaded whenever the 'core' package is imported,
# which happens when Django starts.
__all__ = ('celery_app',)
