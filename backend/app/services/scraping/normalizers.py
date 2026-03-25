from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from app.schemas.lead import ScrapedLead


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return " ".join(text.split())


def normalize_phone_number(phone: Any) -> str | None:
    text = normalize_text(phone)
    if text is None:
        return None
    digits = "".join(character for character in text if character.isdigit())
    if not digits:
        return None
    if digits.startswith("62"):
        digits = "0" + digits[2:]
    elif not digits.startswith("0"):
        digits = "0" + digits
    return digits


def normalize_website(value: Any) -> str | None:
    website = normalize_text(value)
    if website is None:
        return None
    if website.startswith("http://") or website.startswith("https://"):
        return website
    return f"https://{website}"


def normalize_lead(payload: Mapping[str, Any], *, source: str) -> ScrapedLead | None:
    name = normalize_text(payload.get("name"))
    address = normalize_text(payload.get("address"))
    if not name or not address:
        return None

    website = normalize_website(payload.get("website"))
    rating = normalize_text(payload.get("rating"))
    reference_link = normalize_text(
        payload.get("reference_link") or payload.get("referenceLink")
    )

    return ScrapedLead(
        name=name,
        address=address,
        phone=normalize_phone_number(payload.get("phone")),
        website=website,
        reference_link=reference_link,
        rating=rating,
        has_website=bool(website),
        source=source,
        scraped_at=datetime.now(UTC),
    )


def deduplicate_leads(leads: list[ScrapedLead]) -> list[ScrapedLead]:
    seen: set[tuple[str, str]] = set()
    unique: list[ScrapedLead] = []
    for lead in leads:
        key = (lead.name.casefold(), lead.address.casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(lead)
    return unique
