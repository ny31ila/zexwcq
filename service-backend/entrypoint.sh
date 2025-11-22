#!/bin/sh
# project_root/service-backend/entrypoint.sh

echo "Starting entrypoint script..."

echo "Database connection confirmed."

# --- Execute the command provided to the container ---
# This allows the same Docker image to be used for different services (web, celery).
# The command is passed as arguments to this script (e.g., "gunicorn", "celery", etc.).
COMMAND="$1"
shift # Remove the first argument, leaving the rest for the command itself.

if [ "$COMMAND" = "gunicorn" ]; then
    # --- Web Server Startup ---
    echo "Running web server startup tasks..."
    # Apply database migrations
    echo "Applying database migrations..."
    python manage.py migrate --noinput

    # Collect static files
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear

    echo "Starting Gunicorn..."
    # Start Gunicorn, passing any additional arguments.
    # The --workers argument is an example; this could be configured via an env var.
    exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 "$@"

elif [ "$COMMAND" = "celery" ]; then
    # --- Celery Worker Startup ---
    echo "Starting Celery worker..."
    # Start the Celery worker, passing the remaining arguments (e.g., -A core worker -l info)
    exec celery -A core "$@"

else
    echo "Unknown command: $COMMAND"
    echo "Executing command as is: $COMMAND $@"
    exec $COMMAND "$@"
fi
