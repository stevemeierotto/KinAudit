"""Domain constants for Phase B genealogy claims.

Relationships are source claims (claim_status=source_asserted), not verified
genealogical truth. Paths are not persisted; they are reconstructed later from
relationship claims.
"""

PARENT_ROLE_FATHER = "father"
PARENT_ROLE_MOTHER = "mother"
PARENT_ROLE_PARENT = "parent"

PARENT_ROLES = frozenset(
    {
        PARENT_ROLE_FATHER,
        PARENT_ROLE_MOTHER,
        PARENT_ROLE_PARENT,
    }
)

CLAIM_STATUS_SOURCE_ASSERTED = "source_asserted"

CLAIM_STATUSES = frozenset({CLAIM_STATUS_SOURCE_ASSERTED})
