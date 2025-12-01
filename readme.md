
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

Open the newly created `.env` file in a text editor. The default values are suitable for a local development environment, but you can customize them if needed. Remember to fill in the `DB_NAME`, `DB_USER`, and `DB_PASSWORD` fields.

### 3.3. Build and Run the Application

Use Docker Compose to build the images and start all the services. This command may need to be run with `sudo` if your user is not in the `docker` group.

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

## 6. API Endpoint Documentation

All endpoints are prefixed with `/api`. Authentication is required for most endpoints.

### Account & Authentication

This section covers user management and the authentication flow.

*   **`POST /api/account/register/`**: Create a new user account.
    *   **Request Body:**
        ```json
        {
            "email": "testuser@example.com",
            "password": "strongpassword123",
            "first_name": "Test",
            "last_name": "User",
            "gender": "Male",
            "birth_date": "1370-01-01"
        }
        ```

*   **`POST /api/account/token/`**: Log in to get JWT tokens.
    *   **Request Body:**
        ```json
        {
            "email": "testuser@example.com",
            "password": "strongpassword123"
        }
        ```

*   **`POST /api/account/token/refresh/`**: Refresh an expired access token.
    *   **Request Body:**
        ```json
        {
            "refresh": "<your_refresh_token>"
        }
        ```

*   **`GET, PUT /api/account/profile/`**: Get or update the authenticated user's profile.
    *   **Authentication:** Requires a valid `access` token.
    *   **PUT/PATCH Request Body:** All fields are optional.
        ```json
        {
            "email": "new.email@example.com",
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "gender": "Female",
            "birth_date": "1375-05-10"
        }
        ```

### Assessments

*   `GET /api/assessment/packages/`: List all available test packages.
*   `GET /api/assessment/packages/<id>/`: Get details of a specific test package.
*   `GET /api/assessment/assessments/`: List all available assessments.
*   `GET /api/assessment/assessments/<id>/`: Get details of a specific assessment.
*   `GET /api/assessment/attempts/`: List all of the user's past assessment attempts.

*   **`POST /api/assessment/assessments/<assessment_id>/attempt/start/`**: Start a new assessment attempt.
    *   **Request Body:** This endpoint expects an empty request body.
        ```json
        {}
        ```

*   **`POST /api/assessment/assessments/<assessment_id>/attempt/submit/`**: Submit the completed assessment.
    *   **Request Body:** This endpoint expects an empty request body.
        ```json
        {}
        ```

*   **`PATCH /api/assessment/assessments/<assessment_id>/attempt/save-response/`**: Save a response for the current attempt.
    *   This endpoint is used to incrementally save the user's answers. The `response_data` payload format is specific to each assessment.

    *   **Request Body Wrapper:**
        ```json
        {
            "response_data": {
                // Assessment-specific content goes here
            }
        }
        ```

    *   **1. DISC Assessment Format (`assessment_id`: 1)**
        ```json
        "response_data": {
            "1": { "most_like_me": "D", "least_like_me": "I" },
            "2": { "most_like_me": "S", "least_like_me": "C" }
        }
        ```

    *   **2. Gardner Assessment Format (`assessment_id`: 2)**
        ```json
        "response_data": {
            "1": { "response": "5" },
            "2": { "response": "3" }
        }
        ```

    *   **3. Holland (RIASEC) Assessment Format (`assessment_id`: 3)**
        ```json
        "response_data": {
            "interests_____realistic_____1": { "response": true },
            "self_assessment_1_____1": { "response": "4" }
        }
        ```

    *   **4. MBTI Assessment Format (`assessment_id`: 4)**
        ```json
        "response_data": {
            "1": { "response": "a" },
            "2": { "response": "b" }
        }
        ```

    *   **5. NEO (Five-Factor) Assessment Format (`assessment_id`: 5)**
        ```json
        "response_data": {
            "1": { "response": "4" },
            "2": { "response": "1" }
        }
        ```

    *   **6. PVQ (Schwartz Values) Assessment Format (`assessment_id`: 6)**
        ```json
        "response_data": {
            "1": { "response": "2" },
            "2": { "response": "6" }
        }
        ```

    *   **7. Swanson (ADHD) Assessment Format (`assessment_id`: 7)**
        ```json
        "response_data": {
            "1": { "response": "3" },
            "2": { "response": "0" }
        }
        ```

### AI Integration

*   `GET /api/ai-integration/available-models/`: Get a list of available AI models for integration.

*   **`POST /api/assessment/packages/<package_id>/send-to-ai/`**: Manually trigger sending package results to the AI.
    *   **Request Body:**
        ```json
        {
            "provider_model_key": "ollama.gpt_oss_20b"
        }
        ```

### Resume

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
                }
            ]
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
