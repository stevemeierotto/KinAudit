import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.domain.enums import PARENT_ROLE_FATHER, PARENT_ROLE_MOTHER, PARENT_ROLE_PARENT
from app.sources.errors import (
    SourceAuthenticationError,
    SourcePersonMerged,
    SourcePersonNotFound,
    SourceRateLimited,
    SourceResponseInvalid,
)
from app.sources.familysearch.adapter import FamilySearchAdapter
from app.sources.familysearch.auth import StaticAccessTokenProvider
from app.sources.familysearch.client import FamilySearchClient
from app.sources.familysearch.normalize import (
    normalize_parents_payload,
    normalize_person_payload,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "familysearch"
RETRIEVED_AT = datetime(2026, 9, 24, 15, 0, 0, tzinfo=timezone.utc)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_normalize_person_from_fixture() -> None:
    person = normalize_person_payload(
        _load("person_alice.json"),
        retrieved_at=RETRIEVED_AT,
        expected_external_id="PPPJ-MYZ",
    )
    assert person.provider == "familysearch"
    assert person.external_id == "PPPJ-MYZ"
    assert person.claimed_display_name == "Alice Example"
    assert person.claimed_sex == "Female"
    assert person.claimed_birth_text == "about 1810"
    assert person.claimed_death_text == "1888"
    assert person.retrieved_at == RETRIEVED_AT


def test_external_id_preserved_exactly() -> None:
    payload = {
        "persons": [{"id": " L66G-X33 ", "names": []}],
    }
    person = normalize_person_payload(
        payload,
        retrieved_at=RETRIEVED_AT,
        expected_external_id=" L66G-X33 ",
    )
    assert person.external_id == " L66G-X33 "


def test_parents_without_explicit_role_remain_parent_despite_sex() -> None:
    claims = normalize_parents_payload(
        _load("parents_no_explicit_role.json"),
        child_external_id="pid-3",
        retrieved_at=RETRIEVED_AT,
    )
    assert len(claims) == 2
    by_parent = {c.parent_external_id: c for c in claims}

    male_parent = by_parent["FJP-M4RK"]
    assert male_parent.parent_person is not None
    assert male_parent.parent_person.claimed_sex == "Male"
    assert male_parent.parent_role == PARENT_ROLE_PARENT
    assert male_parent.external_claim_key == "P1PPPX-PP0"

    female_parent = by_parent["JRW-NMSD"]
    assert female_parent.parent_person is not None
    assert female_parent.parent_person.claimed_sex == "Female"
    assert female_parent.parent_role == PARENT_ROLE_PARENT
    assert female_parent.external_claim_key == "P2PPPX-PP0"


def test_explicit_parental_roles_map_to_father_mother() -> None:
    claims = normalize_parents_payload(
        _load("parents_explicit_roles.json"),
        child_external_id="pid-3",
        retrieved_at=RETRIEVED_AT,
    )
    by_key = {c.external_claim_key: c for c in claims}
    assert by_key["REL-FATHER-1"].parent_role == PARENT_ROLE_FATHER
    assert by_key["REL-MOTHER-1"].parent_role == PARENT_ROLE_MOTHER


def test_provider_relationship_ids_preserved() -> None:
    claims = normalize_parents_payload(
        _load("parents_no_explicit_role.json"),
        child_external_id="pid-3",
        retrieved_at=RETRIEVED_AT,
    )
    keys = {c.external_claim_key for c in claims}
    assert keys == {"P1PPPX-PP0", "P2PPPX-PP0"}


def test_malformed_person_payload() -> None:
    with pytest.raises(SourceResponseInvalid):
        normalize_person_payload({}, retrieved_at=RETRIEVED_AT)


def _adapter_with_transport(handler: httpx.MockTransport) -> FamilySearchAdapter:
    http = httpx.Client(transport=handler)
    client = FamilySearchClient(
        StaticAccessTokenProvider("test-token"),
        api_base_url="https://api.familysearch.org",
        http_client=http,
    )
    return FamilySearchAdapter(
        StaticAccessTokenProvider("test-token"),
        client=client,
        clock=lambda: RETRIEVED_AT,
    )


def test_adapter_maps_401_to_authentication_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    adapter = _adapter_with_transport(httpx.MockTransport(handler))
    with pytest.raises(SourceAuthenticationError):
        adapter.get_person("PPPJ-MYZ")


def test_adapter_maps_404_and_410_to_not_found() -> None:
    def handler_404(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing")

    def handler_410(request: httpx.Request) -> httpx.Response:
        return httpx.Response(410, text="deleted")

    with pytest.raises(SourcePersonNotFound):
        _adapter_with_transport(httpx.MockTransport(handler_404)).get_person("X")
    with pytest.raises(SourcePersonNotFound):
        _adapter_with_transport(httpx.MockTransport(handler_410)).get_person("X")


def test_adapter_maps_301_to_merged_with_location() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            301,
            headers={"Location": "https://api.familysearch.org/platform/tree/persons/NEW-1"},
            text="moved",
        )

    with pytest.raises(SourcePersonMerged) as exc_info:
        _adapter_with_transport(httpx.MockTransport(handler)).get_person("OLD-1")
    assert exc_info.value.location.endswith("/persons/NEW-1")
    assert exc_info.value.diagnostic is not None


def test_adapter_maps_429_to_rate_limited() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    with pytest.raises(SourceRateLimited):
        _adapter_with_transport(httpx.MockTransport(handler)).get_person("PPPJ-MYZ")


def test_adapter_get_person_with_mocked_http() -> None:
    person_payload = _load("person_alice.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Accept"] == "application/x-fs-v1+json"
        assert request.url.path.endswith("/persons/PPPJ-MYZ")
        return httpx.Response(200, json=person_payload)

    adapter = _adapter_with_transport(httpx.MockTransport(handler))
    person = adapter.get_person("PPPJ-MYZ")
    assert person.external_id == "PPPJ-MYZ"
    assert person.claimed_display_name == "Alice Example"
