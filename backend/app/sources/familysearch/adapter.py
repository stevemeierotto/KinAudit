"""FamilySearch genealogy source adapter."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone

from app.sources.familysearch.auth import AccessTokenProvider
from app.sources.familysearch.client import DEFAULT_API_BASE_URL, FamilySearchClient
from app.sources.familysearch.normalize import (
    PROVIDER,
    normalize_parents_payload,
    normalize_person_payload,
)
from app.sources.normalized import NormalizedParentClaim, NormalizedPerson, PersonWithParents


class FamilySearchAdapter:
    """Retrieves FamilySearch persons/parents and returns normalized objects."""

    def __init__(
        self,
        token_provider: AccessTokenProvider,
        *,
        api_base_url: str = DEFAULT_API_BASE_URL,
        client: FamilySearchClient | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._client = client or FamilySearchClient(
            token_provider, api_base_url=api_base_url
        )
        self._owns_client = client is None
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def provider_key(self) -> str:
        return PROVIDER

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get_person(self, external_id: str) -> NormalizedPerson:
        payload = self._client.get_json(
            f"/platform/tree/persons/{external_id}",
            external_id=external_id,
        )
        return normalize_person_payload(
            payload,
            retrieved_at=self._clock(),
            expected_external_id=external_id,
        )

    def get_parent_claims(
        self, child_external_id: str
    ) -> Sequence[NormalizedParentClaim]:
        payload = self._client.get_json(
            f"/platform/tree/persons/{child_external_id}/parents",
            external_id=child_external_id,
        )
        return normalize_parents_payload(
            payload,
            child_external_id=child_external_id,
            retrieved_at=self._clock(),
        )

    def get_person_with_parents(self, external_id: str) -> PersonWithParents:
        person = self.get_person(external_id)
        claims = tuple(self.get_parent_claims(external_id))
        return PersonWithParents(person=person, parent_claims=claims)
