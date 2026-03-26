from __future__ import annotations

import asyncio
import json

from app.core.config import Settings
from app.services.scraping.providers.google_maps import GoogleMapsScrapeProvider


class _DummySelector:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def get(self) -> str | None:
        return self._value


class _DummyResponse:
    def __init__(
        self,
        *,
        href: str | None,
        html_content: str,
        text_content: str | None = None,
        url: str = "https://www.google.com/maps/search/test",
    ) -> None:
        self._href = href
        self.html_content = html_content
        self._text_content = text_content if text_content is not None else html_content
        self.url = url

    def css(self, _selector: str) -> _DummySelector:
        return _DummySelector(self._href)

    def get_all_text(self) -> str:
        return self._text_content


def _build_result_entry(
    *,
    name: str,
    address: str,
    rating: float | None,
    website: str | None,
    phone: str | None,
    email: str | None,
    place_id: str,
) -> list[object]:
    details: list[object] = [None] * 40
    details[2] = address.split(", ")
    details[4] = [None, None, None, None, None, None, None, rating]
    if website is not None:
        details[7] = [f"/url?q={website}&opi=1", website.removeprefix("https://"), None, "token"]
    details[10] = "0x2e69f1076e78f19f:0xf97da87c79406d61"
    details[11] = name
    details[18] = f"{name}, {address}"
    details[39] = address
    details.extend(
        [
            place_id,
            [phone, None, None, None, None, [f"tel:{phone.replace(' ', '')}"]] if phone else None,
            email,
        ]
    )
    return [None, details]


def test_extract_prefetch_path_uses_selector_then_regex_fallback() -> None:
    provider = GoogleMapsScrapeProvider(settings=Settings())

    selector_response = _DummyResponse(
        href="/search?tbm=map&amp;q=coffee",
        html_content="",
    )
    fallback_response = _DummyResponse(
        href=None,
        html_content='<html><head><link href="/search?tbm=map&amp;q=coffee" as="fetch"></head></html>',
    )

    assert provider._extract_prefetch_path(selector_response) == "/search?tbm=map&q=coffee"
    assert provider._extract_prefetch_path(fallback_response) == "/search?tbm=map&q=coffee"


def test_parse_results_payload_maps_google_payload_into_raw_leads() -> None:
    provider = GoogleMapsScrapeProvider(settings=Settings())
    payload: list[object] = [None] * 65
    payload[64] = [
        _build_result_entry(
            name="First Crack Coffee",
            address="Jl. Bumi No.10, Gunung, South Jakarta City, Jakarta 12120, Indonesia",
            rating=4.8,
            website="https://firstcrackcoffee.id/",
            phone="+62 21 72793835",
            email="hello@firstcrackcoffee.id",
            place_id="ChIJn_F4bgfxaS4RYW1AeXyoffk",
        ),
        _build_result_entry(
            name="Koultoura Coffee",
            address="Jl. Ciniru I No.1, West Rawa, Kebayoran Baru, Jakarta 12180, Indonesia",
            rating=4.7,
            website=None,
            phone="+62 812-8686-9082",
            email=None,
            place_id="ChIJ1234567890abcdef",
        ),
    ]

    results = provider._parse_results_payload(")]}'\n" + json.dumps(payload))

    assert results == [
        {
            "name": "First Crack Coffee",
            "address": "Jl. Bumi No.10, Gunung, South Jakarta City, Jakarta 12120, Indonesia",
            "phone": "+62 21 72793835",
            "email": "hello@firstcrackcoffee.id",
            "website": "https://firstcrackcoffee.id/",
            "reference_link": "https://www.google.com/maps/place/?q=place_id:ChIJn_F4bgfxaS4RYW1AeXyoffk",
            "rating": "4.8",
        },
        {
            "name": "Koultoura Coffee",
            "address": "Jl. Ciniru I No.1, West Rawa, Kebayoran Baru, Jakarta 12180, Indonesia",
            "phone": "+62 812-8686-9082",
            "email": None,
            "website": None,
            "reference_link": "https://www.google.com/maps/place/?q=place_id:ChIJ1234567890abcdef",
            "rating": "4.7",
        },
    ]


def test_scrape_populates_email_from_business_website() -> None:
    provider = GoogleMapsScrapeProvider(settings=Settings())

    async def fake_fetch(url: str) -> _DummyResponse:
        if "google.com/maps/search" in url:
            return _DummyResponse(
                href="/search?tbm=map&q=coffee",
                html_content="",
                url=url,
            )
        if "tbm=map" in url:
            payload: list[object] = [None] * 65
            payload[64] = [
                _build_result_entry(
                    name="Atlas Coffee",
                    address="Seattle, WA",
                    rating=4.9,
                    website="https://atlascoffee.example",
                    phone="+1 206 555 0199",
                    email=None,
                    place_id="ChIJatlascoffee",
                )
            ]
            return _DummyResponse(
                href=None,
                html_content="",
                text_content=")]}'\n" + json.dumps(payload),
                url=url,
            )
        return _DummyResponse(
            href=None,
            html_content='<a href="mailto:hello@atlascoffee.example">Email</a>',
            url=url,
        )

    provider._fetch = fake_fetch  # type: ignore[method-assign]

    results = asyncio.run(provider.scrape(query="Atlas Coffee Seattle", max_results=5))

    assert len(results) == 1
    assert results[0].email == "hello@atlascoffee.example"
