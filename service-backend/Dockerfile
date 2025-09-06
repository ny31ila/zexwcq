# project_root/service-backend/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Enable pip cache mount (Docker BuildKit feature)
# This helps speed up repeated builds by caching downloaded packages
# Requires Docker BuildKit to be enabled (DOCKER_BUILDKIT=1 or Docker Desktop)
# ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# ENV PIP_NO_CACHE_DIR=0

# Set work directory
WORKDIR /app

# Install system dependencies (if needed for specific packages like Pillow, psycopg2)
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         # postgresql-client \
#         # build-essential \
#         # libpq-dev \
#         # libjpeg-dev \
#         # zlib1g-dev \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# --- Install Python dependencies with cache (BuildKit) ---
# This line uses the cache mount if BuildKit is enabled.
# If not, it falls back to standard pip caching within the build context.
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
# (This is overridden by the volume mount in docker-compose for development,
#  but is used during image build and is necessary for production builds)
COPY . /app/

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Collect static files (if needed, adjust settings.py accordingly)
# This is now handled in entrypoint.sh for more flexibility
# RUN python manage.py collectstatic --noinput

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the default command to run the entrypoint script
# The entrypoint script will handle migrations, collectstatic, and starting the server
CMD ["./entrypoint.sh"]
