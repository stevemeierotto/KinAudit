"""Genealogy source adapters and provider-neutral contracts."""

from app.sources.errors import (
    SourceAuthenticationError,
    SourceAuthorizationError,
    SourceError,
    SourceNetworkError,
    SourcePersonMerged,
    SourcePersonNotFound,
    SourceRateLimited,
    SourceResponseInvalid,
    SourceUnavailable,
)
from app.sources.normalized import (
    NormalizedParentClaim,
    NormalizedPerson,
    PersonWithParents,
)
from app.sources.protocol import GenealogySourceAdapter

__all__ = [
    "GenealogySourceAdapter",
    "NormalizedParentClaim",
    "NormalizedPerson",
    "PersonWithParents",
    "SourceAuthenticationError",
    "SourceAuthorizationError",
    "SourceError",
    "SourceNetworkError",
    "SourcePersonMerged",
    "SourcePersonNotFound",
    "SourceRateLimited",
    "SourceResponseInvalid",
    "SourceUnavailable",
]
