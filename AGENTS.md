# KinAudit Agent Instructions

## Project

KinAudit is a source-neutral genealogy research and auditing application.

It will ingest genealogy data from external sources, normalize that data into
an internal model, analyze ancestral relationships, identify gaps and potential
problems, preserve evidence and provenance, and present findings for human review.

FamilySearch is the first planned data source. KinAudit must not be designed as
a FamilySearch-specific application.

## Authoritative Documentation

Before making architectural or genealogy-domain changes, read:

- `docs/ARCHITECTURE.md`
- `docs/GENEALOGY_RULES.md`

If implementation conflicts with those documents, stop and identify the conflict
rather than silently changing the architecture or domain rules.

## Planned Stack

- Frontend: React + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL
- ORM/migrations: SQLAlchemy + Alembic
- Containers: Docker + Docker Compose
- API: REST/JSON

These are current architectural decisions. Do not replace them without explicit
approval.

## Development Workflow

For substantial changes:

PLAN -> REVIEW -> LOCK -> IMPLEMENT -> TEST -> STOP

Before implementation:

1. Inspect the existing repository.
2. Identify affected files.
3. State assumptions.
4. Describe the proposed change.
5. Identify risks.
6. Define tests and exit criteria.

Do not begin implementation until explicitly authorized when the task is in
planning/review mode.

## Scope Discipline

Make the smallest change that satisfies the approved task.

Do not:

- redesign unrelated parts of the repository
- introduce speculative abstractions
- add dependencies without justification
- introduce microservices without a demonstrated need
- perform unrelated cleanup
- change genealogy invariants to simplify implementation
- introduce an LLM where deterministic code can solve the problem
- communicate with external genealogy APIs directly from the frontend

## Architectural Boundary

The intended direction is:

React/Vite
    |
FastAPI
    |
KinAudit domain + analysis
    |
Source adapters
    |
External genealogy/record services

External providers are data sources, not KinAudit's domain model.

Provider-specific authentication, identifiers, request/response formats, and
API behavior belong behind source adapters.

## Genealogy Safety

KinAudit analyzes genealogy; it does not silently decide genealogy.

Never:

- infer parentage from matching names or compatible dates alone
- merge people solely because their attributes look similar
- silently repair conflicting source data
- discard independent ancestral paths to the same person
- treat missing information as contradictory information
- automatically modify an external genealogy tree

Analysis should produce findings for human review.

See `docs/GENEALOGY_RULES.md` for the complete domain rules.

## Testing

Tests should protect behavior and domain invariants rather than implementation
details.

Every bug fix should include a regression test when practical.

Important genealogy cases include:

- repeated names belonging to different people
- one ancestor reached through multiple paths
- missing parents
- conflicting evidence
- questionable chronology
- traversal stopping because of a configured generation limit

## Current Stage

KinAudit is at the repository-skeleton stage.

The first objective is not to build the complete application.

The initial vertical slice will eventually be:

starting person
    -> retrieve ancestry
    -> normalize data
    -> persist people and relationships
    -> identify ancestry gaps
    -> return/display findings

Until that work is explicitly approved, concentrate on establishing a clean,
minimal foundation.
