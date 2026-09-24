"""Deterministic genealogy invariants for Phase B."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.enums import (
    CLAIM_STATUS_SOURCE_ASSERTED,
    PARENT_ROLE_FATHER,
    PARENT_ROLE_MOTHER,
)
from app.domain.models import ExternalIdentity, Person, Relationship


def _person_with_identity(
    session: Session,
    *,
    provider: str,
    external_id: str,
    retrieved_at: datetime,
    display_name: str | None = None,
) -> tuple[Person, ExternalIdentity]:
    person = Person()
    session.add(person)
    session.flush()
    identity = ExternalIdentity(
        person_id=person.id,
        provider=provider,
        external_id=external_id,
        retrieved_at=retrieved_at,
        claimed_display_name=display_name,
    )
    session.add(identity)
    session.flush()
    return person, identity


def test_identical_names_remain_distinct_people(
    db_session: Session, retrieved_at: datetime
) -> None:
    person_a, identity_a = _person_with_identity(
        db_session,
        provider="familysearch",
        external_id="AAAA-111",
        retrieved_at=retrieved_at,
        display_name="John Morgan",
    )
    person_b, identity_b = _person_with_identity(
        db_session,
        provider="familysearch",
        external_id="BBBB-222",
        retrieved_at=retrieved_at,
        display_name="John Morgan",
    )

    assert person_a.id != person_b.id
    assert identity_a.claimed_display_name == identity_b.claimed_display_name == "John Morgan"
    assert identity_a.external_id != identity_b.external_id


def test_one_person_may_have_multiple_external_identities(
    db_session: Session, retrieved_at: datetime
) -> None:
    person = Person()
    db_session.add(person)
    db_session.flush()

    fs = ExternalIdentity(
        person_id=person.id,
        provider="familysearch",
        external_id="L66G-X33",
        retrieved_at=retrieved_at,
        claimed_display_name="Jane Example",
    )
    archive = ExternalIdentity(
        person_id=person.id,
        provider="archive",
        external_id="L66G-X33",  # same textual id, different provider
        retrieved_at=retrieved_at,
        claimed_display_name="Jane Example",
    )
    db_session.add_all([fs, archive])
    db_session.flush()

    assert fs.person_id == archive.person_id == person.id
    assert fs.id != archive.id


def test_duplicate_provider_external_id_rejected(
    db_session: Session, retrieved_at: datetime
) -> None:
    person_a = Person()
    person_b = Person()
    db_session.add_all([person_a, person_b])
    db_session.flush()

    db_session.add(
        ExternalIdentity(
            person_id=person_a.id,
            provider="familysearch",
            external_id="L66G-X33",
            retrieved_at=retrieved_at,
        )
    )
    db_session.flush()

    db_session.add(
        ExternalIdentity(
            person_id=person_b.id,
            provider="familysearch",
            external_id="L66G-X33",
            retrieved_at=retrieved_at,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_conflicting_relationship_claims_coexist(
    db_session: Session, retrieved_at: datetime
) -> None:
    child = Person()
    father_a = Person()
    father_b = Person()
    db_session.add_all([child, father_a, father_b])
    db_session.flush()

    claim_a = Relationship(
        child_person_id=child.id,
        parent_person_id=father_a.id,
        parent_role=PARENT_ROLE_FATHER,
        claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
        provider="familysearch",
        source_external_id="CHILD-1",
        retrieved_at=retrieved_at,
    )
    claim_b = Relationship(
        child_person_id=child.id,
        parent_person_id=father_b.id,
        parent_role=PARENT_ROLE_FATHER,
        claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
        provider="archive",
        source_external_id="CHILD-1-ALT",
        retrieved_at=retrieved_at,
    )
    db_session.add_all([claim_a, claim_b])
    db_session.flush()

    assert claim_a.id != claim_b.id
    assert claim_a.parent_person_id != claim_b.parent_person_id


def test_external_ids_preserve_exact_value(
    db_session: Session, retrieved_at: datetime
) -> None:
    exact_id = "L66G-X33"
    odd_id = " abC-123 "
    person = Person()
    db_session.add(person)
    db_session.flush()

    identity = ExternalIdentity(
        person_id=person.id,
        provider="familysearch",
        external_id=exact_id,
        retrieved_at=retrieved_at,
    )
    other = ExternalIdentity(
        person_id=person.id,
        provider="archive",
        external_id=odd_id,
        retrieved_at=retrieved_at,
    )
    db_session.add_all([identity, other])
    db_session.flush()
    db_session.expire_all()

    loaded = db_session.get(ExternalIdentity, identity.id)
    loaded_odd = db_session.get(ExternalIdentity, other.id)
    assert loaded is not None
    assert loaded_odd is not None
    assert loaded.external_id == "L66G-X33"
    assert loaded_odd.external_id == " abC-123 "


def test_provenance_survives_persistence_and_retrieval(
    db_session: Session, retrieved_at: datetime
) -> None:
    child = Person()
    parent = Person()
    db_session.add_all([child, parent])
    db_session.flush()

    identity = ExternalIdentity(
        person_id=child.id,
        provider="familysearch",
        external_id="CHILD-XYZ",
        retrieved_at=retrieved_at,
        claimed_display_name="William Example",
    )
    claim = Relationship(
        child_person_id=child.id,
        parent_person_id=parent.id,
        parent_role=PARENT_ROLE_MOTHER,
        claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
        provider="familysearch",
        source_external_id="CHILD-XYZ",
        external_claim_key="provider-supplied-claim-99",
        retrieved_at=retrieved_at,
    )
    db_session.add_all([identity, claim])
    db_session.flush()
    db_session.expire_all()

    loaded_identity = db_session.get(ExternalIdentity, identity.id)
    loaded_claim = db_session.get(Relationship, claim.id)
    assert loaded_identity is not None
    assert loaded_claim is not None
    assert loaded_identity.provider == "familysearch"
    assert loaded_identity.external_id == "CHILD-XYZ"
    assert loaded_identity.retrieved_at == retrieved_at
    assert loaded_claim.provider == "familysearch"
    assert loaded_claim.source_external_id == "CHILD-XYZ"
    assert loaded_claim.external_claim_key == "provider-supplied-claim-99"
    assert loaded_claim.retrieved_at == retrieved_at


def test_deleting_person_with_identity_is_restricted(
    db_session: Session, retrieved_at: datetime
) -> None:
    person, _identity = _person_with_identity(
        db_session,
        provider="familysearch",
        external_id="KEEP-ME",
        retrieved_at=retrieved_at,
    )
    db_session.flush()

    db_session.delete(person)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_person_with_relationship_is_restricted(
    db_session: Session, retrieved_at: datetime
) -> None:
    child = Person()
    parent = Person()
    db_session.add_all([child, parent])
    db_session.flush()
    db_session.add(
        Relationship(
            child_person_id=child.id,
            parent_person_id=parent.id,
            parent_role=PARENT_ROLE_FATHER,
            claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
            provider="familysearch",
            retrieved_at=retrieved_at,
        )
    )
    db_session.flush()

    db_session.delete(child)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_external_claim_key_rejected(
    db_session: Session, retrieved_at: datetime
) -> None:
    child = Person()
    parent_a = Person()
    parent_b = Person()
    db_session.add_all([child, parent_a, parent_b])
    db_session.flush()

    db_session.add(
        Relationship(
            child_person_id=child.id,
            parent_person_id=parent_a.id,
            parent_role=PARENT_ROLE_FATHER,
            claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
            provider="familysearch",
            external_claim_key="CLAIM-1",
            retrieved_at=retrieved_at,
        )
    )
    db_session.flush()

    db_session.add(
        Relationship(
            child_person_id=child.id,
            parent_person_id=parent_b.id,
            parent_role=PARENT_ROLE_FATHER,
            claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
            provider="familysearch",
            external_claim_key="CLAIM-1",
            retrieved_at=retrieved_at,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_null_external_claim_keys_may_coexist(
    db_session: Session, retrieved_at: datetime
) -> None:
    child = Person()
    parent_a = Person()
    parent_b = Person()
    db_session.add_all([child, parent_a, parent_b])
    db_session.flush()

    db_session.add_all(
        [
            Relationship(
                child_person_id=child.id,
                parent_person_id=parent_a.id,
                parent_role=PARENT_ROLE_FATHER,
                claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
                provider="familysearch",
                external_claim_key=None,
                retrieved_at=retrieved_at,
            ),
            Relationship(
                child_person_id=child.id,
                parent_person_id=parent_b.id,
                parent_role=PARENT_ROLE_FATHER,
                claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
                provider="familysearch",
                external_claim_key=None,
                retrieved_at=retrieved_at,
            ),
        ]
    )
    db_session.flush()


def test_self_parent_relationship_rejected(
    db_session: Session, retrieved_at: datetime
) -> None:
    person = Person()
    db_session.add(person)
    db_session.flush()

    db_session.add(
        Relationship(
            child_person_id=person.id,
            parent_person_id=person.id,
            parent_role=PARENT_ROLE_FATHER,
            claim_status=CLAIM_STATUS_SOURCE_ASSERTED,
            provider="familysearch",
            retrieved_at=retrieved_at,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
