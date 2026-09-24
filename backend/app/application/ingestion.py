"""Ingest normalized source data into Phase B persistence models."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import CLAIM_STATUS_SOURCE_ASSERTED
from app.domain.models import ExternalIdentity, Person, Relationship
from app.sources.normalized import NormalizedParentClaim, NormalizedPerson
from app.sources.protocol import GenealogySourceAdapter


class SourceIngestionService:
    """Persists normalized provider data without provider-specific knowledge."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_person_identity(self, normalized: NormalizedPerson) -> Person:
        identity = self._session.scalar(
            select(ExternalIdentity).where(
                ExternalIdentity.provider == normalized.provider,
                ExternalIdentity.external_id == normalized.external_id,
            )
        )
        if identity is None:
            person = Person()
            self._session.add(person)
            self._session.flush()
            identity = ExternalIdentity(
                person_id=person.id,
                provider=normalized.provider,
                external_id=normalized.external_id,
                retrieved_at=normalized.retrieved_at,
                claimed_display_name=normalized.claimed_display_name,
                claimed_sex=normalized.claimed_sex,
                claimed_birth_text=normalized.claimed_birth_text,
                claimed_death_text=normalized.claimed_death_text,
            )
            self._session.add(identity)
            self._session.flush()
            return person

        identity.retrieved_at = normalized.retrieved_at
        identity.claimed_display_name = normalized.claimed_display_name
        identity.claimed_sex = normalized.claimed_sex
        identity.claimed_birth_text = normalized.claimed_birth_text
        identity.claimed_death_text = normalized.claimed_death_text
        self._session.flush()
        person = self._session.get(Person, identity.person_id)
        assert person is not None
        return person

    def ingest_parent_claims(
        self, claims: Sequence[NormalizedParentClaim]
    ) -> list[Relationship]:
        results: list[Relationship] = []
        for claim in claims:
            results.append(self._ingest_one_parent_claim(claim))
        return results

    def import_person_and_parents(
        self, adapter: GenealogySourceAdapter, external_id: str
    ) -> tuple[Person, list[Relationship]]:
        bundle = adapter.get_person_with_parents(external_id)
        person = self.upsert_person_identity(bundle.person)
        relationships = self.ingest_parent_claims(bundle.parent_claims)
        return person, relationships

    def _ingest_one_parent_claim(self, claim: NormalizedParentClaim) -> Relationship:
        child_person = self.upsert_person_identity(
            NormalizedPerson(
                provider=claim.provider,
                external_id=claim.child_external_id,
                retrieved_at=claim.retrieved_at,
            )
        )
        if claim.parent_person is not None:
            parent_person = self.upsert_person_identity(claim.parent_person)
        else:
            parent_person = self.upsert_person_identity(
                NormalizedPerson(
                    provider=claim.provider,
                    external_id=claim.parent_external_id,
                    retrieved_at=claim.retrieved_at,
                )
            )

        existing = self._find_existing_relationship(claim, child_person, parent_person)
        if existing is not None:
            existing.parent_role = claim.parent_role
            existing.claim_status = CLAIM_STATUS_SOURCE_ASSERTED
            existing.source_external_id = claim.source_external_id
            existing.retrieved_at = claim.retrieved_at
            if claim.external_claim_key is not None:
                existing.external_claim_key = claim.external_claim_key
            self._session.flush()
            return existing

        relationship = Relationship(
            child_person_id=child_person.id,
            parent_person_id=parent_person.id,
            parent_role=claim.parent_role,
            claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
            provider=claim.provider,
            source_external_id=claim.source_external_id,
            external_claim_key=claim.external_claim_key,
            retrieved_at=claim.retrieved_at,
        )
        self._session.add(relationship)
        self._session.flush()
        return relationship

    def _find_existing_relationship(
        self,
        claim: NormalizedParentClaim,
        child_person: Person,
        parent_person: Person,
    ) -> Relationship | None:
        if claim.external_claim_key is not None:
            return self._session.scalar(
                select(Relationship).where(
                    Relationship.provider == claim.provider,
                    Relationship.external_claim_key == claim.external_claim_key,
                )
            )

        return self._session.scalar(
            select(Relationship).where(
                Relationship.provider == claim.provider,
                Relationship.child_person_id == child_person.id,
                Relationship.parent_person_id == parent_person.id,
                Relationship.parent_role == claim.parent_role,
                Relationship.external_claim_key.is_(None),
            )
        )
