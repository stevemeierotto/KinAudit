# KinAudit

Source-neutral genealogy research, auditing, and analysis platform.

See `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/GENEALOGY_RULES.md` for
project rules and architecture.

## Current stage

Phase C — source adapter foundation. FamilySearch person/parents retrieval is
normalized and ingested into Phase B models through a service layer. There is
no genealogy HTTP API, crawl, or analysis yet.

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

## Database migrations

From `backend/`, with PostgreSQL reachable (for example via Compose) and
`DATABASE_URL` set (see `.env.example`):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
```

Useful Alembic commands:

```bash
alembic current
alembic downgrade base
alembic upgrade head
```

KinAudit UUID primary keys are generated in the Python/SQLAlchemy layer. The
initial migration does not enable `pgcrypto` or `uuid-ossp`.

## Backend tests

With PostgreSQL up and migrations applied (tests also run `alembic upgrade head`
once per session when the database is reachable):

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

- Phase A health tests do not require genealogy tables.
- Phase B genealogy invariant tests require real PostgreSQL.
- Phase C FamilySearch adapter/ingestion tests use fixtures and mocked HTTP;
  they make **no live FamilySearch calls**.

## FamilySearch (Phase C)

Source adapters live under `backend/app/sources/`. Persistence goes through
`SourceIngestionService` (`backend/app/application/ingestion.py`).

Development token injection (optional, for manual live experiments only):

| Variable | Purpose |
|----------|---------|
| `FAMILYSEARCH_API_BASE_URL` | API host (default production) |
| `FAMILYSEARCH_ACCESS_TOKEN` | Pre-obtained Bearer token (never commit) |
| `FAMILYSEARCH_CLIENT_ID` | OAuth app key (future OAuth flow) |
| `FAMILYSEARCH_REDIRECT_URI` | Registered redirect URI (future OAuth flow) |

Phase C does not implement the OAuth browser login flow.

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
