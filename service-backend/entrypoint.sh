#!/bin/sh
# project_root/service-backend/entrypoint.sh

echo "Starting entrypoint script..."

# Check if the database file exists (for SQLite dev setup)
# This check might be different if using PostgreSQL
if [ ! -f "db.sqlite3" ]; then
    echo "Database file not found. Running migrations..."
    python manage.py migrate --noinput
else
    echo "Database file found. Applying migrations..."
    python manage.py migrate --noinput
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# --- Determine the command to run based on an environment variable or argument ---
# This allows the same image to be used for different services (web server, celery worker)
# Default command is to run the Django development server
CMD="${1:-runserver}"
echo "Executing command: $CMD"

if [ "$CMD" = "runserver" ]; then
    echo "Starting Django development server..."
    # Use 0.0.0.0:8000 to make it accessible from outside the container
    # --insecure allows serving static files with runserver (not for production)
    exec python manage.py runserver 0.0.0.0:8000 --insecure
elif [ "$CMD" = "celery" ]; then
    echo "Starting Celery worker..."
    # The actual celery command will be passed by docker-compose
    # This part of the script might not be reached if docker-compose overrides CMD
    # But it's good practice to have a general entrypoint
    exec "$@"
else
    echo "Unknown command: $CMD"
    exit 1
fi
