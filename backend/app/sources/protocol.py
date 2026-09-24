"""Provider-neutral genealogy source adapter contract."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from app.sources.normalized import NormalizedParentClaim, NormalizedPerson, PersonWithParents


@runtime_checkable
class GenealogySourceAdapter(Protocol):
    """Smallest contract for retrieving a person and their parent claims."""

    @property
    def provider_key(self) -> str: ...

    def get_person(self, external_id: str) -> NormalizedPerson: ...

    def get_parent_claims(
        self, child_external_id: str
    ) -> Sequence[NormalizedParentClaim]: ...

    def get_person_with_parents(self, external_id: str) -> PersonWithParents: ...
