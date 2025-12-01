
# Nexa Backend Project

## 1. Project Overview

This is the backend service for the Nexa platform, a comprehensive career and personal development application. It provides a RESTful API for managing user accounts, assessments, resumes, skills, career resources, and counseling services. The project is built with Django and is fully containerized using Docker for consistent development and deployment.

## 2. Prerequisites

Before you begin, ensure you have the following software installed on your local machine:

*   **Docker:** [Installation Guide](https://docs.docker.com/engine/install/)
*   **Docker Compose:** [Installation Guide](https://docs.docker.com/compose/install/)

## 3. Getting Started

Follow these steps to get the project up and running on your local system.

### 3.1. Clone the Repository

```bash
git clone https://github.com/example-org/nexa-backend.git
cd nexa-backend
```

### 3.2. Set Up Environment Variables

The project uses an `.env` file to manage all required environment variables. A template is provided in the root directory.

**1. Create the `.env` file:**

```bash
cp .env.template .env
```

**2. Review and update the `.env` file:**

Open the newly created `.env` file in a text editor. The default values are suitable for a local development environment, but you can customize them if needed.

### 3.3. Build and Run the Application

Use Docker Compose to build the images and start all the services. This command needs to be run with `sudo` because the Docker daemon requires root privileges.

```bash
sudo docker compose up --build
```

This command will start all the services in the background, including the Django application, PostgreSQL database, Redis, Celery, Nginx, Prometheus, and Grafana.

## 4. Running the Application & Services

Once the `docker compose up` command finishes, the application and its related services will be running and accessible at the following local URLs:

| Service               | Local URL                     | Description                               |
| --------------------- | ----------------------------- | ----------------------------------------- |
| **Nginx (Main Entry)**| `http://localhost:80`         | Main entry point for the API.             |
| **Grafana**           | `http://localhost:3000`       | Dashboard for viewing application metrics.|
| **Prometheus**        | `http://localhost:9090`       | Collects and stores application metrics.  |

You can view the logs for all running services using:

```bash
sudo docker compose logs -f
```

## 5. Running Tests

To ensure your environment is set up correctly and to verify the application's integrity, run the full test suite. A helper script is provided to simplify this process.

Execute the following command from the project root:

```bash
sudo docker compose run --rm service-backend sh -c "./scripts/run-tests.sh"
```

A successful run will show a list of tests that passed and end with an "OK" message.

## 6. API Authentication Flow (User Story)

The API is secured using JSON Web Tokens (JWT). A new mobile developer needs to follow this flow to interact with protected endpoints.

### Step 1: Register a New User

First, a new user must be created.

*   **Endpoint:** `POST /api/account/register/`
*   **Request Body:**

    ```json
    {
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    ```

*   **Success Response (201 Created):**

    ```json
    {
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
    ```

### Step 2: Log In to Get Tokens

After registration, the user logs in with their credentials to obtain access and refresh tokens.

*   **Endpoint:** `POST /api/account/token/`
*   **Request Body:**

    ```json
    {
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "refresh": "eyJhbGciOiJI...",
        "access": "eyJhbGciOiJI..."
    }
    ```

### Step 3: Access Protected Endpoints

The `access` token is used to authenticate with all protected API endpoints. It must be included in the `Authorization` header as a Bearer token.

*   **Example Header:**

    ```
    Authorization: Bearer <your_access_token>
    ```

If the token is expired or invalid, the API will return a `401 Unauthorized` error.

### Step 4: Refresh the Access Token

Access tokens are short-lived. Once an access token expires, the `refresh` token can be used to get a new one without requiring the user to log in again.

*   **Endpoint:** `POST /api/account/token/refresh/`
*   **Request Body:**

    ```json
    {
        "refresh": "<your_refresh_token>"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "access": "eyJhbGciOiJI..."
    }
    ```

## 7. API Endpoint Documentation

All endpoints are prefixed with `/api`. Authentication is required for most endpoints.

### Account

*   `POST /api/account/register/`: Create a new user account.
*   `POST /api/account/token/`: Log in and receive JWT tokens.
*   `POST /api/account/token/refresh/`: Refresh an expired access token.
*   `GET, PUT /api/account/profile/`: Get or update the authenticated user's profile.

### Assessments

*   `GET /api/assessment/packages/`: List all available test packages.
*   `GET /api/assessment/packages/<id>/`: Get details of a specific test package.
*   `GET /api/assessment/assessments/`: List all available assessments.
*   `GET /api/assessment/assessments/<id>/`: Get details of a specific assessment.
*   `POST /api/assessment/assessments/<assessment_id>/attempt/start/`: Start a new assessment attempt.
*   `PATCH /api/assessment/assessments/<assessment_id>/attempt/save-response/`: Save a response for the current attempt.
*   `POST /api/assessment/assessments/<assessment_id>/attempt/submit/`: Submit the completed assessment.
*   `GET /api/assessment/attempts/`: List all of the user's past assessment attempts.

### AI Integration

*   `GET /api/ai-integration/available-models/`: Get a list of available AI models for integration.

### Resume

This section manages user resumes.

*   `GET /api/resume/`: List all of the user's resumes.
*   `POST /api/resume/create/`: Create a new resume.
    *   **Request Body Example:**
        ```json
        {
            "title": "Software Engineer Resume",
            "personal_info": {
                "full_name": "Test User",
                "email": "testuser@example.com",
                "phone": "123-456-7890"
            },
            "sections": [
                {
                    "title": "Summary",
                    "content": "Experienced software engineer..."
                },
                {
                    "title": "Experience",
                    "content": "Software Engineer at Tech Company..."
                }
            ]
        }
        ```
    *   **Success Response (201 Created):**
        ```json
        {
            "id": 1,
            "title": "Software Engineer Resume",
            "personal_info": { ... },
            "sections": [ ... ],
            "created_at": "2023-10-27T10:00:00Z"
        }
        ```
*   `GET, PUT, DELETE /api/resume/<id>/`: Get, update, or delete a specific resume.
*   `GET /api/resume/<resume_id>/generate-pdf/`: Generate a PDF version of a resume.

### Skills & Courses

*   `GET /api/skill/categories/`: List all skill categories.
*   `GET /api/skill/courses/`: List all available courses.
*   `GET /api/skill/courses/category/<category_id>/`: List courses within a specific category.

### Career & Business

*   `GET /api/career/jobs/`: List all open job positions.
*   `GET /api/career/jobs/<id>/`: Get details of a specific job opening.
*   `GET /api/career/resources/`: List available business resources.
*   `GET /api/career/resources/<id>/`: Get details of a specific business resource.

### Counseling

*   `GET /api/counseling/consultants/`: List all available consultants.
*   `GET /api/counseling/consultants/<id>/`: Get details of a specific consultant.
*   `GET /api/counseling/appointments/my/`: List the user's scheduled appointments.
*   `POST /api/counseling/appointments/book/`: Book a new appointment with a consultant.
*   `POST /api/counseling/appointments/<appointment_id>/cancel/`: Cancel an existing appointment.

### Content

*   `GET /api/content/news/`: Get a list of the latest news articles.
*   `GET /api/content/news/<id>/`: Get the details of a specific news article.
