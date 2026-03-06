## Project Context

This document summarizes the key aspects of the `gestor_de_custos` project for easier onboarding and maintenance.

### Docker Configuration

The project uses `docker-compose` to manage the development and production environments. The main configuration files are:

- `docker-compose.yml`: For the development environment.
- `docker-compose.production.yml`: For the production environment.

The development environment consists of the following services:
- `db`: A PostgreSQL database.
- `redis`: A Redis instance.
- `mailpit`: An email testing tool.
- `app`: The FastAPI backend application.
- `celery-worker`: A Celery worker for background tasks.
- `celery-beat`: A Celery beat for scheduled tasks.
- `frontend`: A Node.js container for the Vue.js frontend.

### Environment Variables

The project requires a `.env` file in the root directory to store environment variables. A `.env.example` file is provided with the required variables.

### Backend

The backend is a FastAPI application located in the `app/` directory. It uses `uv` for dependency management.

Key dependencies include:
- `fastapi`
- `sqlalchemy`
- `celery`
- `alembic`

### Tasks and Scripts

The project uses `taskipy` to run tasks. The available tasks are defined in the `[tool.taskipy.tasks]` section of the `pyproject.toml` file.

Common tasks include:
- `task up`: Starts the development environment.
- `task down`: Stops the development environment.
- `task logs`: Shows the logs of the running containers.
- `task test`: Runs the tests.
- `task lint`: Lints the code.

### Database Migrations

Database migrations are handled by `alembic`. The `entrypoint.sh` script runs the migrations automatically when the `app` container starts.

### Background Tasks

The project uses Celery for background tasks. The `celery-worker` and `celery-beat` services run the Celery processes.
