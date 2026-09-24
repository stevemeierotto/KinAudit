"""Persistence round-trips for the Phase B genealogy model."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import CLAIM_STATUS_SOURCE_ASSERTED, PARENT_ROLE_FATHER
from app.domain.models import ExternalIdentity, Person, Relationship


def test_parent_child_relationship_persists(
    db_session: Session, retrieved_at: datetime
) -> None:
    child = Person()
    father = Person()
    db_session.add_all([child, father])
    db_session.flush()

    claim = Relationship(
        child_person_id=child.id,
        parent_person_id=father.id,
        parent_role=PARENT_ROLE_FATHER,
        claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
        provider="familysearch",
        source_external_id="CHILD-001",
        external_claim_key=None,
        retrieved_at=retrieved_at,
    )
    db_session.add(claim)
    db_session.flush()

    loaded = db_session.get(Relationship, claim.id)
    assert loaded is not None
    assert loaded.child_person_id == child.id
    assert loaded.parent_person_id == father.id
    assert loaded.parent_role == PARENT_ROLE_FATHER
    assert loaded.claim_status == CLAIM_STATUS_SOURCE_ASSERTED
    assert loaded.provider == "familysearch"
    assert loaded.source_external_id == "CHILD-001"
    assert loaded.external_claim_key is None
    assert loaded.retrieved_at == retrieved_at


def test_person_uuid_generated_in_application_layer(db_session: Session) -> None:
    person = Person()
    assert person.id is not None  # default applied before flush via SQLAlchemy default
    db_session.add(person)
    db_session.flush()
    assert db_session.execute(
        select(Person.id).where(Person.id == person.id)
    ).scalar_one() == person.id
