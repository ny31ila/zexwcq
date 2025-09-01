# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Collect static files (if needed, adjust settings.py accordingly)
# RUN python manage.py collectstatic --noinput

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
# Use Gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
# For development, you might use:
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]