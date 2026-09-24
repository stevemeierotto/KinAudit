"""Provider-neutral source adapter errors."""

from __future__ import annotations


class SourceError(Exception):
    """Base error for genealogy source adapters."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        external_id: str | None = None,
        diagnostic: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.external_id = external_id
        self.diagnostic = diagnostic


class SourceAuthenticationError(SourceError):
    """Authentication failed (e.g. missing/invalid token)."""


class SourceAuthorizationError(SourceError):
    """Authenticated but not permitted."""


class SourcePersonNotFound(SourceError):
    """Person/profile not found or deleted at the provider."""


class SourcePersonMerged(SourceError):
    """Person was merged into another person at the provider."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        external_id: str | None = None,
        diagnostic: str | None = None,
        location: str | None = None,
    ) -> None:
        super().__init__(
            message,
            provider=provider,
            external_id=external_id,
            diagnostic=diagnostic,
        )
        self.location = location


class SourceRateLimited(SourceError):
    """Provider rate-limited the request."""


class SourceUnavailable(SourceError):
    """Provider returned a server error or is otherwise unavailable."""


class SourceNetworkError(SourceError):
    """Transport failure before a usable HTTP response."""


class SourceResponseInvalid(SourceError):
    """Provider response could not be normalized."""
