#!/bin/sh
# project_root/service-backend/entrypoint.sh

echo "Starting entrypoint script for production..."

# --- Wait for the database to be ready ---
# The script will wait for the PostgreSQL service to be available before proceeding.
# It uses a small Python script to poll the DB_HOST and DB_PORT.
# These environment variables must be available to the container.

echo "Waiting for database..."
# The python:slim image doesn't have netcat, so we use a python script to check the connection.
python << END
import socket
import time
import os

host = os.environ.get("DB_HOST")
port = int(os.environ.get("DB_PORT", 5432))

while True:
    try:
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set a timeout for the connection attempt
            s.settimeout(1)
            # Attempt to connect
            s.connect((host, port))
        # If connection is successful, break the loop
        print("Database is ready!")
        break
    except (socket.error, socket.timeout) as ex:
        # If connection fails, wait and retry
        print(f"Database isn't ready yet, waiting... ({ex})")
        time.sleep(1)
END

echo "Database connection confirmed."

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# --- Start Gunicorn ---
# The 'exec' command is used to replace the current shell process with the Gunicorn process.
# This is a best practice for containerization as it allows signals (like SIGTERM for stopping)
# to be passed directly to the application, enabling graceful shutdowns.
echo "Starting Gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
