"""FamilySearch HTTP client and status mapping."""

from __future__ import annotations

from typing import Any

import httpx

from app.sources.errors import (
    SourceAuthenticationError,
    SourceAuthorizationError,
    SourceNetworkError,
    SourcePersonMerged,
    SourcePersonNotFound,
    SourceRateLimited,
    SourceUnavailable,
)
from app.sources.familysearch.auth import AccessTokenProvider

PROVIDER = "familysearch"
DEFAULT_ACCEPT = "application/x-fs-v1+json"
DEFAULT_API_BASE_URL = "https://api.familysearch.org"


class FamilySearchClient:
    def __init__(
        self,
        token_provider: AccessTokenProvider,
        *,
        api_base_url: str = DEFAULT_API_BASE_URL,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._token_provider = token_provider
        self._api_base_url = api_base_url.rstrip("/")
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def get_json(self, path: str, *, external_id: str | None = None) -> dict[str, Any]:
        url = f"{self._api_base_url}{path}"
        headers = {
            "Accept": DEFAULT_ACCEPT,
            "Authorization": f"Bearer {self._token_provider.get_access_token()}",
        }
        try:
            response = self._http.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise SourceNetworkError(
                f"FamilySearch network error: {exc}",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=str(exc),
            ) from None

        return self._handle_response(response, external_id=external_id)

    def _handle_response(
        self, response: httpx.Response, *, external_id: str | None
    ) -> dict[str, Any]:
        status = response.status_code
        diagnostic = _safe_diagnostic(response)

        if status == 200:
            try:
                payload = response.json()
            except ValueError:
                raise SourceUnavailable(
                    "FamilySearch returned non-JSON success body",
                    provider=PROVIDER,
                    external_id=external_id,
                    diagnostic=diagnostic,
                ) from None
            if not isinstance(payload, dict):
                raise SourceUnavailable(
                    "FamilySearch returned unexpected JSON root type",
                    provider=PROVIDER,
                    external_id=external_id,
                    diagnostic=diagnostic,
                )
            return payload

        if status == 204:
            return {}

        if status == 301:
            location = response.headers.get("Location")
            raise SourcePersonMerged(
                "FamilySearch person was merged into another person",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=diagnostic,
                location=location,
            )

        if status in (404, 410):
            raise SourcePersonNotFound(
                "FamilySearch person was not found",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=diagnostic,
            )

        if status == 401:
            raise SourceAuthenticationError(
                "FamilySearch authentication failed",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=diagnostic,
            )

        if status == 403:
            raise SourceAuthorizationError(
                "FamilySearch authorization failed",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=diagnostic,
            )

        if status == 429:
            raise SourceRateLimited(
                "FamilySearch rate-limited the request",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=diagnostic,
            )

        if status >= 500:
            raise SourceUnavailable(
                f"FamilySearch unavailable (HTTP {status})",
                provider=PROVIDER,
                external_id=external_id,
                diagnostic=diagnostic,
            )

        raise SourceUnavailable(
            f"FamilySearch unexpected HTTP status {status}",
            provider=PROVIDER,
            external_id=external_id,
            diagnostic=diagnostic,
        )


def _safe_diagnostic(response: httpx.Response, limit: int = 500) -> str:
    parts = [f"status={response.status_code}"]
    location = response.headers.get("Location")
    if location:
        parts.append(f"location={location}")
    body = (response.text or "").strip().replace("\n", " ")
    if body:
        parts.append(f"body={body[:limit]}")
    return "; ".join(parts)
