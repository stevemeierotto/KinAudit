# KinAudit

Source-neutral genealogy research, auditing, and analysis platform.

See `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/GENEALOGY_RULES.md` for
project rules and architecture.

## Current stage

Phase A — repository foundation. The stack runs frontend, backend, and
PostgreSQL with health checks. No genealogy functionality yet.

## Prerequisites

- Docker and Docker Compose

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service  | URL                    |
|----------|------------------------|
| Frontend | http://localhost:5173  |
| Backend  | http://localhost:8001  |
| Postgres | localhost:5432         |

The backend container listens on port 8000 internally. The host publish
mapping is `8001:8000` so the stack can run alongside services that already
use host port 8000.

Health endpoints:

- `GET /health` — liveness
- `GET /health/ready` — readiness (PostgreSQL reachable → 200, else 503)

## Backend tests

From the repository root, with dependencies installed:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Liveness tests run without PostgreSQL. Readiness tests that need a database
expect `DATABASE_URL` (default Compose credentials on localhost work when
Postgres is up).

## Configuration

Copy `.env.example` to `.env` and adjust as needed. Documented variables:

| Variable            | Purpose                                      |
|---------------------|----------------------------------------------|
| `POSTGRES_USER`     | PostgreSQL user                              |
| `POSTGRES_PASSWORD` | PostgreSQL password                          |
| `POSTGRES_DB`       | PostgreSQL database name                     |
| `DATABASE_URL`      | SQLAlchemy URL used by the backend           |
| `ENVIRONMENT`       | Runtime environment label                    |
| `BACKEND_HOST`      | Backend bind host                            |
| `BACKEND_PORT`      | Backend bind port                            |
| `VITE_API_BASE_URL` | Browser API base URL for the frontend        |
