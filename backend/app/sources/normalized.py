"""Source-neutral transfer types between adapters and ingestion.

These are not SQLAlchemy models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NormalizedPerson:
    provider: str
    external_id: str
    retrieved_at: datetime
    claimed_display_name: str | None = None
    claimed_sex: str | None = None
    claimed_birth_text: str | None = None
    claimed_death_text: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedParentClaim:
    provider: str
    child_external_id: str
    parent_external_id: str
    parent_role: str
    retrieved_at: datetime
    source_external_id: str | None = None
    external_claim_key: str | None = None
    parent_person: NormalizedPerson | None = None


@dataclass(frozen=True, slots=True)
class PersonWithParents:
    person: NormalizedPerson
    parent_claims: tuple[NormalizedParentClaim, ...] = field(default_factory=tuple)
