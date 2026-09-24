import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.ingestion import SourceIngestionService
from app.domain.enums import PARENT_ROLE_FATHER, PARENT_ROLE_PARENT
from app.domain.models import ExternalIdentity, Person, Relationship
from app.sources.familysearch.adapter import FamilySearchAdapter
from app.sources.familysearch.auth import StaticAccessTokenProvider
from app.sources.familysearch.client import FamilySearchClient
from app.sources.normalized import NormalizedParentClaim, NormalizedPerson

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "familysearch"
RETRIEVED_AT = datetime(2026, 9, 24, 16, 0, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 25, 16, 0, 0, tzinfo=timezone.utc)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _adapter_for_routes(routes: dict[str, dict]) -> FamilySearchAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        for suffix, payload in routes.items():
            if path.endswith(suffix):
                return httpx.Response(200, json=payload)
        return httpx.Response(404, text="missing route")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = FamilySearchClient(
        StaticAccessTokenProvider("test-token"),
        http_client=http,
    )
    return FamilySearchAdapter(
        StaticAccessTokenProvider("test-token"),
        client=client,
        clock=lambda: RETRIEVED_AT,
    )


def test_import_person_and_parents_vertical_slice(db_session: Session) -> None:
    adapter = _adapter_for_routes(
        {
            "/persons/pid-3": {
                "persons": [
                    {
                        "id": "pid-3",
                        "names": [
                            {
                                "preferred": True,
                                "nameForms": [{"fullText": "Child Example"}],
                            }
                        ],
                    }
                ]
            },
            "/persons/pid-3/parents": _load("parents_no_explicit_role.json"),
        }
    )
    service = SourceIngestionService(db_session)
    person, relationships = service.import_person_and_parents(adapter, "pid-3")

    assert person.id is not None
    assert len(relationships) == 2
    assert all(r.parent_role == PARENT_ROLE_PARENT for r in relationships)
    assert db_session.scalar(select(func.count()).select_from(Person)) == 3
    assert db_session.scalar(select(func.count()).select_from(ExternalIdentity)) == 3
    assert db_session.scalar(select(func.count()).select_from(Relationship)) == 2


def test_repeated_identity_ingestion_reuses_person(db_session: Session) -> None:
    service = SourceIngestionService(db_session)
    first = service.upsert_person_identity(
        NormalizedPerson(
            provider="familysearch",
            external_id="PPPJ-MYZ",
            retrieved_at=RETRIEVED_AT,
            claimed_display_name="Alice Example",
        )
    )
    second = service.upsert_person_identity(
        NormalizedPerson(
            provider="familysearch",
            external_id="PPPJ-MYZ",
            retrieved_at=LATER,
            claimed_display_name="Alice Example Updated",
            claimed_sex="Female",
        )
    )
    assert first.id == second.id
    identity = db_session.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.provider == "familysearch",
            ExternalIdentity.external_id == "PPPJ-MYZ",
        )
    )
    assert identity is not None
    assert identity.claimed_display_name == "Alice Example Updated"
    assert identity.claimed_sex == "Female"
    assert identity.retrieved_at == LATER
    assert db_session.scalar(select(func.count()).select_from(Person)) == 1
    assert db_session.scalar(select(func.count()).select_from(ExternalIdentity)) == 1


def test_no_name_based_person_merge(db_session: Session) -> None:
    service = SourceIngestionService(db_session)
    a = service.upsert_person_identity(
        NormalizedPerson(
            provider="familysearch",
            external_id="CHILD-1",
            retrieved_at=RETRIEVED_AT,
            claimed_display_name="Same Name Person",
        )
    )
    b = service.upsert_person_identity(
        NormalizedPerson(
            provider="familysearch",
            external_id="CHILD-2",
            retrieved_at=RETRIEVED_AT,
            claimed_display_name="Same Name Person",
        )
    )
    assert a.id != b.id
    assert db_session.scalar(select(func.count()).select_from(Person)) == 2


def test_conflicting_parent_claims_coexist(db_session: Session) -> None:
    service = SourceIngestionService(db_session)
    service.upsert_person_identity(
        NormalizedPerson(
            provider="familysearch",
            external_id="CHILD",
            retrieved_at=RETRIEVED_AT,
        )
    )
    claims = [
        NormalizedParentClaim(
            provider="familysearch",
            child_external_id="CHILD",
            parent_external_id="FATHER-A",
            parent_role=PARENT_ROLE_FATHER,
            retrieved_at=RETRIEVED_AT,
            external_claim_key="CLAIM-A",
            parent_person=NormalizedPerson(
                provider="familysearch",
                external_id="FATHER-A",
                retrieved_at=RETRIEVED_AT,
                claimed_display_name="Father A",
            ),
        ),
        NormalizedParentClaim(
            provider="familysearch",
            child_external_id="CHILD",
            parent_external_id="FATHER-B",
            parent_role=PARENT_ROLE_FATHER,
            retrieved_at=RETRIEVED_AT,
            external_claim_key="CLAIM-B",
            parent_person=NormalizedPerson(
                provider="familysearch",
                external_id="FATHER-B",
                retrieved_at=RETRIEVED_AT,
                claimed_display_name="Father B",
            ),
        ),
    ]
    rows = service.ingest_parent_claims(claims)
    assert len(rows) == 2
    assert rows[0].parent_person_id != rows[1].parent_person_id
    assert db_session.scalar(select(func.count()).select_from(Relationship)) == 2


def test_relationship_claim_key_upsert(db_session: Session) -> None:
    service = SourceIngestionService(db_session)
    first = service.ingest_parent_claims(
        [
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=RETRIEVED_AT,
                external_claim_key="REL-1",
                source_external_id="CHILD",
            )
        ]
    )[0]
    second = service.ingest_parent_claims(
        [
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=LATER,
                external_claim_key="REL-1",
                source_external_id="CHILD",
            )
        ]
    )[0]
    assert first.id == second.id
    assert second.retrieved_at == LATER
    assert db_session.scalar(select(func.count()).select_from(Relationship)) == 1


def test_null_key_relationship_refresh(db_session: Session) -> None:
    service = SourceIngestionService(db_session)
    first = service.ingest_parent_claims(
        [
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=RETRIEVED_AT,
                external_claim_key=None,
            )
        ]
    )[0]
    second = service.ingest_parent_claims(
        [
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=LATER,
                external_claim_key=None,
            )
        ]
    )[0]
    assert first.id == second.id
    assert second.retrieved_at == LATER
    assert db_session.scalar(select(func.count()).select_from(Relationship)) == 1


def test_missing_relationship_on_later_response_does_not_delete(
    db_session: Session,
) -> None:
    service = SourceIngestionService(db_session)
    service.ingest_parent_claims(
        [
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT-A",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=RETRIEVED_AT,
                external_claim_key="KEEP-ME",
            ),
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT-B",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=RETRIEVED_AT,
                external_claim_key="ALSO-KEEP",
            ),
        ]
    )
    # Later response only includes one claim; old claim must remain.
    service.ingest_parent_claims(
        [
            NormalizedParentClaim(
                provider="familysearch",
                child_external_id="CHILD",
                parent_external_id="PARENT-A",
                parent_role=PARENT_ROLE_PARENT,
                retrieved_at=LATER,
                external_claim_key="KEEP-ME",
            )
        ]
    )
    assert db_session.scalar(select(func.count()).select_from(Relationship)) == 2
