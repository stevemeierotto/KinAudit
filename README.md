# KinAudit

Source-neutral genealogy research, auditing, and analysis platform.

See `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/GENEALOGY_RULES.md` for
project rules and architecture.

## Current stage

Phase B — canonical genealogy model. The stack includes Phase A services plus
PostgreSQL persistence for `people`, `external_identities`, and `relationships`
(source claims with provenance). No source adapters or genealogy analysis yet.

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
- Genealogy invariant tests require real PostgreSQL and exercise uniqueness,
  provenance, conflicting claims, and `ON DELETE RESTRICT` behavior.

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
