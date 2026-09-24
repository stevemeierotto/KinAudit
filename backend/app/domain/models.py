from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.domain.enums import CLAIM_STATUS_SOURCE_ASSERTED


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Person(Base):
    """Canonical KinAudit person identity. Independent of any provider ID."""

    __tablename__ = "people"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    external_identities: Mapped[list[ExternalIdentity]] = relationship(
        back_populates="person"
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("id", _uuid())
        kwargs.setdefault("created_at", _utcnow())
        kwargs.setdefault("updated_at", _utcnow())
        super().__init__(**kwargs)


class ExternalIdentity(Base):
    """Associates a KinAudit person with a provider-supplied external profile."""

    __tablename__ = "external_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            name="uq_external_identities_provider_external_id",
        ),
        Index("ix_external_identities_person_id", "person_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("people.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    claimed_display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_sex: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_birth_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_death_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    person: Mapped[Person] = relationship(back_populates="external_identities")

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("id", _uuid())
        kwargs.setdefault("created_at", _utcnow())
        kwargs.setdefault("updated_at", _utcnow())
        super().__init__(**kwargs)


class Relationship(Base):
    """A parent-child relationship claim asserted by a source.

    Multiple claims about the same child (including conflicting parents) may
    coexist. claim_status is source_asserted only in Phase B.
    """

    __tablename__ = "relationships"
    __table_args__ = (
        CheckConstraint(
            "child_person_id <> parent_person_id",
            name="ck_relationships_child_ne_parent",
        ),
        CheckConstraint(
            "parent_role IN ('father', 'mother', 'parent')",
            name="ck_relationships_parent_role",
        ),
        CheckConstraint(
            "claim_status IN ('source_asserted')",
            name="ck_relationships_claim_status",
        ),
        Index("ix_relationships_child_person_id", "child_person_id"),
        Index("ix_relationships_parent_person_id", "parent_person_id"),
        Index(
            "ix_relationships_child_person_id_parent_role",
            "child_person_id",
            "parent_role",
        ),
        Index(
            "uq_relationships_provider_external_claim_key",
            "provider",
            "external_claim_key",
            unique=True,
            postgresql_where=text("external_claim_key IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    child_person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("people.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("people.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_role: Mapped[str] = mapped_column(Text, nullable=False)
    claim_status: Mapped[str] = mapped_column(
        Text, nullable=False, default=CLAIM_STATUS_SOURCE_ASSERTED
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    source_external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_claim_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("id", _uuid())
        kwargs.setdefault("claim_status", CLAIM_STATUS_SOURCE_ASSERTED)
        kwargs.setdefault("created_at", _utcnow())
        kwargs.setdefault("updated_at", _utcnow())
        super().__init__(**kwargs)
