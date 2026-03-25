from __future__ import annotations

from app.services.scraping.normalizers import (
    deduplicate_leads,
    normalize_lead,
    normalize_phone_number,
)


def test_normalize_phone_number_handles_indonesian_prefixes() -> None:
    assert normalize_phone_number("+62 812-3456-789") == "08123456789"
    assert normalize_phone_number("8123456789") == "08123456789"


def test_normalize_lead_maps_legacy_shape() -> None:
    lead = normalize_lead(
        {
            "name": "Coffee House",
            "address": "Jl. Sudirman No. 1, Jakarta",
            "phone": "+62 812-3456-789",
            "website": "coffehouse.example",
            "referenceLink": "https://google.com/maps/place/example",
            "rating": "4.7",
        },
        source="google_maps",
    )

    assert lead is not None
    assert lead.phone == "08123456789"
    assert lead.website == "https://coffehouse.example"
    assert lead.reference_link == "https://google.com/maps/place/example"
    assert lead.has_website is True


def test_deduplicate_leads_uses_name_and_address() -> None:
    first = normalize_lead(
        {"name": "Coffee House", "address": "Jakarta"},
        source="google_maps",
    )
    duplicate = normalize_lead(
        {"name": "coffee house", "address": "jakarta"},
        source="google_maps",
    )
    second = normalize_lead(
        {"name": "Tea House", "address": "Bandung"},
        source="google_maps",
    )

    assert first is not None
    assert duplicate is not None
    assert second is not None

    unique = deduplicate_leads([first, duplicate, second])

    assert len(unique) == 2
