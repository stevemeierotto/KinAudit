"""FamilySearch access-token providers (Phase C: static/env only)."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from app.sources.errors import SourceAuthenticationError

PROVIDER = "familysearch"


@runtime_checkable
class AccessTokenProvider(Protocol):
    def get_access_token(self) -> str: ...


class StaticAccessTokenProvider:
    """Supplies a pre-obtained Bearer access token."""

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token.strip()

    def get_access_token(self) -> str:
        if not self._access_token:
            raise SourceAuthenticationError(
                "FamilySearch access token is empty",
                provider=PROVIDER,
            )
        return self._access_token


class EnvironmentAccessTokenProvider:
    """Reads FAMILYSEARCH_ACCESS_TOKEN from the environment."""

    def __init__(self, env_var: str = "FAMILYSEARCH_ACCESS_TOKEN") -> None:
        self._env_var = env_var

    def get_access_token(self) -> str:
        token = (os.environ.get(self._env_var) or "").strip()
        if not token:
            raise SourceAuthenticationError(
                f"Environment variable {self._env_var} is not set",
                provider=PROVIDER,
            )
        return token
