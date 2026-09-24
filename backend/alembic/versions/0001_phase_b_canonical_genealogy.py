"""Phase B canonical genealogy model.

Revision ID: 0001_phase_b
Revises:
Create Date: 2026-09-24

Creates people, external_identities, and relationships only.
UUID values are generated in the application layer, not by database extensions.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_phase_b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "people",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "external_identities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_display_name", sa.Text(), nullable=True),
        sa.Column("claimed_sex", sa.Text(), nullable=True),
        sa.Column("claimed_birth_text", sa.Text(), nullable=True),
        sa.Column("claimed_death_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "external_id",
            name="uq_external_identities_provider_external_id",
        ),
    )
    op.create_index(
        "ix_external_identities_person_id",
        "external_identities",
        ["person_id"],
        unique=False,
    )

    op.create_table(
        "relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("child_person_id", sa.Uuid(), nullable=False),
        sa.Column("parent_person_id", sa.Uuid(), nullable=False),
        sa.Column("parent_role", sa.Text(), nullable=False),
        sa.Column("claim_status", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("source_external_id", sa.Text(), nullable=True),
        sa.Column("external_claim_key", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "child_person_id <> parent_person_id",
            name="ck_relationships_child_ne_parent",
        ),
        sa.CheckConstraint(
            "parent_role IN ('father', 'mother', 'parent')",
            name="ck_relationships_parent_role",
        ),
        sa.CheckConstraint(
            "claim_status IN ('source_asserted')",
            name="ck_relationships_claim_status",
        ),
        sa.ForeignKeyConstraint(
            ["child_person_id"], ["people.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["parent_person_id"], ["people.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_relationships_child_person_id",
        "relationships",
        ["child_person_id"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_parent_person_id",
        "relationships",
        ["parent_person_id"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_child_person_id_parent_role",
        "relationships",
        ["child_person_id", "parent_role"],
        unique=False,
    )
    op.create_index(
        "uq_relationships_provider_external_claim_key",
        "relationships",
        ["provider", "external_claim_key"],
        unique=True,
        postgresql_where=sa.text("external_claim_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_relationships_provider_external_claim_key",
        table_name="relationships",
        postgresql_where=sa.text("external_claim_key IS NOT NULL"),
    )
    op.drop_index(
        "ix_relationships_child_person_id_parent_role",
        table_name="relationships",
    )
    op.drop_index("ix_relationships_parent_person_id", table_name="relationships")
    op.drop_index("ix_relationships_child_person_id", table_name="relationships")
    op.drop_table("relationships")
    op.drop_index("ix_external_identities_person_id", table_name="external_identities")
    op.drop_table("external_identities")
    op.drop_table("people")
