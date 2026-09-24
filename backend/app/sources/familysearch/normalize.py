"""Normalize FamilySearch JSON payloads into source-neutral transfer types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.enums import (
    PARENT_ROLE_FATHER,
    PARENT_ROLE_MOTHER,
    PARENT_ROLE_PARENT,
)
from app.sources.errors import SourceResponseInvalid
from app.sources.normalized import NormalizedParentClaim, NormalizedPerson

PROVIDER = "familysearch"


def normalize_person_payload(
    payload: dict[str, Any],
    *,
    retrieved_at: datetime,
    expected_external_id: str | None = None,
) -> NormalizedPerson:
    persons = payload.get("persons")
    if not isinstance(persons, list) or not persons:
        raise SourceResponseInvalid(
            "FamilySearch person payload missing persons[]",
            provider=PROVIDER,
            external_id=expected_external_id,
        )

    person_obj = persons[0]
    if not isinstance(person_obj, dict):
        raise SourceResponseInvalid(
            "FamilySearch person entry is not an object",
            provider=PROVIDER,
            external_id=expected_external_id,
        )

    external_id = person_obj.get("id")
    if not isinstance(external_id, str) or external_id == "":
        raise SourceResponseInvalid(
            "FamilySearch person missing id",
            provider=PROVIDER,
            external_id=expected_external_id,
        )

    if expected_external_id is not None and external_id != expected_external_id:
        raise SourceResponseInvalid(
            "FamilySearch person id does not match requested external id",
            provider=PROVIDER,
            external_id=expected_external_id,
            diagnostic=f"payload_id={external_id}",
        )

    return NormalizedPerson(
        provider=PROVIDER,
        external_id=external_id,
        retrieved_at=retrieved_at,
        claimed_display_name=_extract_display_name(person_obj),
        claimed_sex=_extract_sex(person_obj),
        claimed_birth_text=_extract_fact_date(person_obj, "http://gedcomx.org/Birth"),
        claimed_death_text=_extract_fact_date(person_obj, "http://gedcomx.org/Death"),
    )


def normalize_parents_payload(
    payload: dict[str, Any],
    *,
    child_external_id: str,
    retrieved_at: datetime,
) -> list[NormalizedParentClaim]:
    persons_by_id = _index_persons(payload.get("persons"))
    relationships = payload.get("relationships")
    if relationships is None:
        return []
    if not isinstance(relationships, list):
        raise SourceResponseInvalid(
            "FamilySearch parents payload has invalid relationships",
            provider=PROVIDER,
            external_id=child_external_id,
        )

    claims: list[NormalizedParentClaim] = []
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        if rel.get("type") != "http://gedcomx.org/ParentChild":
            continue

        parent_id, child_id = _parent_and_child_ids(rel, child_external_id)
        if parent_id is None or child_id != child_external_id:
            continue

        claim_key = rel.get("id")
        if not isinstance(claim_key, str) or claim_key == "":
            claim_key = None

        parent_obj = persons_by_id.get(parent_id)
        parent_person = None
        if parent_obj is not None:
            parent_person = NormalizedPerson(
                provider=PROVIDER,
                external_id=parent_id,
                retrieved_at=retrieved_at,
                claimed_display_name=_extract_display_name(parent_obj),
                claimed_sex=_extract_sex(parent_obj),
                claimed_birth_text=_extract_fact_date(
                    parent_obj, "http://gedcomx.org/Birth"
                ),
                claimed_death_text=_extract_fact_date(
                    parent_obj, "http://gedcomx.org/Death"
                ),
            )

        claims.append(
            NormalizedParentClaim(
                provider=PROVIDER,
                child_external_id=child_external_id,
                parent_external_id=parent_id,
                parent_role=_explicit_parent_role(rel, payload, parent_id),
                retrieved_at=retrieved_at,
                source_external_id=child_external_id,
                external_claim_key=claim_key,
                parent_person=parent_person,
            )
        )

    return claims


def _index_persons(persons: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    if not isinstance(persons, list):
        return indexed
    for person in persons:
        if isinstance(person, dict) and isinstance(person.get("id"), str):
            indexed[person["id"]] = person
    return indexed


def _parent_and_child_ids(
    rel: dict[str, Any], child_external_id: str
) -> tuple[str | None, str | None]:
    person1 = _resource_id(rel.get("person1"))
    person2 = _resource_id(rel.get("person2"))
    if person1 is None or person2 is None:
        return None, None

    links = rel.get("links")
    if isinstance(links, dict):
        parent_from_link = _href_person_id(links.get("parent"))
        child_from_link = _href_person_id(links.get("child"))
        if parent_from_link and child_from_link:
            return parent_from_link, child_from_link

    if person2 == child_external_id:
        return person1, person2
    if person1 == child_external_id:
        return person2, person1
    return None, None


def _resource_id(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    rid = value.get("resourceId")
    if isinstance(rid, str) and rid:
        return rid
    resource = value.get("resource")
    if isinstance(resource, str) and resource.startswith("#") and len(resource) > 1:
        return resource[1:]
    return None


def _href_person_id(link: Any) -> str | None:
    if not isinstance(link, dict):
        return None
    href = link.get("href")
    if not isinstance(href, str) or "/persons/" not in href:
        return None
    pid = href.split("/persons/", 1)[1]
    pid = pid.split("?", 1)[0].strip("/")
    return pid or None


def _explicit_parent_role(
    rel: dict[str, Any], payload: dict[str, Any], parent_id: str
) -> str:
    """Use only explicit parental role claims; never infer from sex/gender."""
    candidates = _collect_role_candidates(rel, payload, parent_id)
    for candidate in candidates:
        mapped = _map_explicit_role(candidate)
        if mapped is not None:
            return mapped
    return PARENT_ROLE_PARENT


def _collect_role_candidates(
    rel: dict[str, Any], payload: dict[str, Any], parent_id: str
) -> list[str]:
    candidates: list[str] = []

    for key in ("role", "parentRole", "parent_role"):
        value = rel.get(key)
        if isinstance(value, str):
            candidates.append(value)
        elif isinstance(value, dict) and isinstance(value.get("type"), str):
            candidates.append(value["type"])

    facts = rel.get("facts")
    if isinstance(facts, list):
        for fact in facts:
            if isinstance(fact, dict) and isinstance(fact.get("type"), str):
                candidates.append(fact["type"])

    caprs = payload.get("childAndParentsRelationships")
    if not isinstance(caprs, list):
        return candidates

    for capr in caprs:
        if not isinstance(capr, dict):
            continue
        for side in ("parent1", "parent2"):
            if _resource_id(capr.get(side)) != parent_id:
                continue
            for facts_key in (f"{side}Facts", f"{side}_facts"):
                side_facts = capr.get(facts_key)
                if isinstance(side_facts, list):
                    for fact in side_facts:
                        if isinstance(fact, dict) and isinstance(fact.get("type"), str):
                            candidates.append(fact["type"])
            role_value = capr.get(f"{side}Role") or capr.get(f"{side}_role")
            if isinstance(role_value, str):
                candidates.append(role_value)
            elif isinstance(role_value, dict) and isinstance(role_value.get("type"), str):
                candidates.append(role_value["type"])

    return candidates


def _map_explicit_role(candidate: str) -> str | None:
    normalized = candidate.strip().lower()
    if (
        normalized in {"father", "http://gedcomx.org/father"}
        or normalized.endswith("/father")
    ):
        return PARENT_ROLE_FATHER
    if (
        normalized in {"mother", "http://gedcomx.org/mother"}
        or normalized.endswith("/mother")
    ):
        return PARENT_ROLE_MOTHER
    return None


def _extract_display_name(person: dict[str, Any]) -> str | None:
    names = person.get("names")
    if not isinstance(names, list):
        return None
    preferred = None
    for name in names:
        if not isinstance(name, dict):
            continue
        if name.get("preferred") is True:
            preferred = name
            break
        if preferred is None:
            preferred = name
    if preferred is None:
        return None
    name_forms = preferred.get("nameForms")
    if not isinstance(name_forms, list) or not name_forms:
        return None
    form = name_forms[0]
    if not isinstance(form, dict):
        return None
    full = form.get("fullText")
    if isinstance(full, str) and full.strip():
        return full
    return None


def _extract_sex(person: dict[str, Any]) -> str | None:
    gender = person.get("gender")
    if isinstance(gender, dict):
        gtype = gender.get("type")
        if isinstance(gtype, str) and gtype:
            if gtype.endswith("/Male"):
                return "Male"
            if gtype.endswith("/Female"):
                return "Female"
            return gtype
    if isinstance(gender, str) and gender:
        return gender
    return None


def _extract_fact_date(person: dict[str, Any], fact_type: str) -> str | None:
    facts = person.get("facts")
    if not isinstance(facts, list):
        return None
    for fact in facts:
        if not isinstance(fact, dict) or fact.get("type") != fact_type:
            continue
        date = fact.get("date")
        if isinstance(date, dict):
            for key in ("original", "formal"):
                value = date.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            normalized = date.get("normalized")
            if isinstance(normalized, list):
                for item in normalized:
                    if isinstance(item, dict):
                        text = item.get("value")
                        if isinstance(text, str) and text.strip():
                            return text
        elif isinstance(date, str) and date.strip():
            return date
    return None
