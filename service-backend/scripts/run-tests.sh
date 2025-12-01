#!/bin/sh
set -e

# This script runs the Django test suite with a dedicated in-memory SQLite3 database.
# It's designed to be run from the Docker container.

echo "Running Django tests..."
python manage.py test --noinput
