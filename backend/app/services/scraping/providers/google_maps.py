from __future__ import annotations

import asyncio
import json
import re
from html import unescape
from typing import Any, Mapping
from urllib.parse import parse_qs, quote, unquote, urljoin, urlsplit

from scrapling import AsyncFetcher

from app.core.config import Settings
from app.schemas.lead import ScrapedLead
from app.services.scraping.normalizers import deduplicate_leads, normalize_lead, normalize_text
from app.services.scraping.providers.base import ScrapeProvider

GOOGLE_MAPS_LANGUAGE = "en"
GOOGLE_MAPS_REGION = "us"
GOOGLE_MAPS_PREFETCH_SELECTOR = 'link[as="fetch"][href*="tbm=map"]::attr(href)'
GOOGLE_REDIRECT_PREFIX = "/url?"
GOOGLE_HOSTS = ("google.com", "maps.google.com", "www.google.com")
NON_WEBSITE_HOSTS = (
    "googleusercontent.com",
    "gstatic.com",
    "googleapis.com",
)
PLACE_ID_PREFIX = "ChI"
TEL_PREFIX = "tel:"
XSSI_PREFIX = ")]}'"
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


class GoogleMapsScrapeProvider(ScrapeProvider):
    source = "google_maps"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def scrape(
        self,
        *,
        query: str,
        max_results: int,
        query_config: Mapping[str, Any] | None = None,
    ) -> list[ScrapedLead]:
        search_url = self._build_search_url(query)

        try:
            initial_response = await self._fetch(search_url)
            payload_path = self._extract_prefetch_path(initial_response)
            payload_response = await self._fetch(urljoin(str(initial_response.url), payload_path))
            raw_results = self._parse_results_payload(payload_response.get_all_text())
        except Exception as exc:
            raise RuntimeError(f"Google Maps scrape failed: {exc}") from exc

        normalized = [
            normalized_lead
            for item in raw_results
            if (normalized_lead := normalize_lead(item, source=self.source)) is not None
        ]
        deduplicated = deduplicate_leads(normalized)[:max_results]
        await self._populate_emails(deduplicated)
        return deduplicated

    def _build_search_url(self, query: str) -> str:
        quoted_query = quote(query)
        return (
            f"https://www.google.com/maps/search/{quoted_query}"
            f"?hl={GOOGLE_MAPS_LANGUAGE}&gl={GOOGLE_MAPS_REGION}"
        )

    async def _fetch(self, url: str) -> Any:
        timeout_seconds = max(self.settings.scraper_timeout_ms / 1000, 1)
        headers = {
            "User-Agent": self.settings.scraper_user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        }
        return await AsyncFetcher.get(
            url,
            headers=headers,
            timeout=timeout_seconds,
            verify=self.settings.scraper_verify_tls,
        )

    def _extract_prefetch_path(self, response: Any) -> str:
        href = response.css(GOOGLE_MAPS_PREFETCH_SELECTOR).get()
        if href:
            return unescape(href)

        match = re.search(r'<link href="([^"]*tbm=map[^"]*)"\s+as="fetch"', response.html_content)
        if match:
            return unescape(match.group(1))

        raise RuntimeError("Google Maps prefetch payload link not found")

    def _parse_results_payload(self, payload_text: str) -> list[dict[str, Any]]:
        text = payload_text.strip()
        if text.startswith(XSSI_PREFIX):
            _, _, text = text.partition("\n")
        if not text:
            return []

        payload = json.loads(text)
        entries = self._find_result_entries(payload)
        return [
            parsed_entry
            for entry in entries
            if (parsed_entry := self._parse_result_entry(entry)) is not None
        ]

    def _find_result_entries(self, payload: Any) -> list[list[Any]]:
        best_match: list[list[Any]] = []
        stack: list[Any] = [payload]

        while stack:
            current = stack.pop()
            if not isinstance(current, list):
                continue

            if current and all(self._is_result_entry(item) for item in current):
                if len(current) > len(best_match):
                    best_match = current

            for child in current:
                if isinstance(child, list):
                    stack.append(child)

        return best_match

    def _is_result_entry(self, entry: Any) -> bool:
        details = self._get_list_item(entry, 1)
        if not isinstance(details, list):
            return False

        name = normalize_text(self._get_list_item(details, 11))
        address = normalize_text(
            self._get_list_item(details, 39)
            or self._get_list_item(details, 18)
            or self._join_address_parts(self._get_list_item(details, 2))
        )
        return bool(name and address)

    def _parse_result_entry(self, entry: Any) -> dict[str, Any] | None:
        details = self._get_list_item(entry, 1)
        if not isinstance(details, list):
            return None

        name = normalize_text(self._get_list_item(details, 11))
        address = normalize_text(
            self._get_list_item(details, 39)
            or self._get_list_item(details, 18)
            or self._join_address_parts(self._get_list_item(details, 2))
        )
        if not name or not address:
            return None

        rating_value = self._get_nested_item(details, 4, 7)
        rating = normalize_text(rating_value)
        website = self._extract_website(details)
        phone = self._extract_phone(details)
        email = self._extract_email(details)

        return {
            "name": name,
            "address": address,
            "phone": phone,
            "email": email,
            "website": website,
            "reference_link": self._build_reference_link(details, name=name, address=address),
            "rating": rating,
        }

    def _build_reference_link(self, details: list[Any], *, name: str, address: str) -> str:
        place_id = next(
            (
                value
                for value in self._walk_strings(details)
                if isinstance(value, str) and value.startswith(PLACE_ID_PREFIX)
            ),
            None,
        )
        if place_id:
            return f"https://www.google.com/maps/place/?q=place_id:{place_id}"

        return f"https://www.google.com/maps/search/{quote(f'{name} {address}')}"

    def _extract_website(self, details: list[Any]) -> str | None:
        for value in self._walk_strings(details):
            if not isinstance(value, str) or not value.startswith(GOOGLE_REDIRECT_PREFIX):
                continue
            decoded = self._decode_google_redirect(value)
            if not decoded:
                continue
            if self._is_external_url(decoded):
                return decoded

        for value in self._walk_strings(details):
            decoded = self._decode_google_redirect(value)
            if not decoded:
                continue
            if self._is_external_url(decoded):
                return decoded

        return None

    def _extract_phone(self, details: list[Any]) -> str | None:
        for value in self._walk_strings(details):
            if not isinstance(value, str):
                continue
            if value.startswith(("http://", "https://", GOOGLE_REDIRECT_PREFIX, "0x", PLACE_ID_PREFIX)):
                continue
            if self._looks_like_phone(value):
                return value

        for value in self._walk_strings(details):
            if isinstance(value, str) and value.startswith(TEL_PREFIX):
                return value.removeprefix(TEL_PREFIX)

        return None

    def _extract_email(self, details: list[Any]) -> str | None:
        for value in self._walk_strings(details):
            if not isinstance(value, str):
                continue
            match = EMAIL_PATTERN.search(value)
            if match:
                return match.group(0).casefold()
        return None

    async def _populate_emails(self, leads: list[ScrapedLead]) -> None:
        await asyncio.gather(
            *(self._populate_email_for_lead(lead) for lead in leads),
            return_exceptions=True,
        )

    async def _populate_email_for_lead(self, lead: ScrapedLead) -> None:
        if lead.email or not lead.website:
            return

        email = await self._fetch_email_from_website(lead.website)
        if email:
            lead.email = email

    async def _fetch_email_from_website(self, website: str) -> str | None:
        try:
            response = await self._fetch(website)
        except Exception:
            return None

        content = " ".join(
            fragment
            for fragment in (
                getattr(response, "html_content", None),
                response.get_all_text() if hasattr(response, "get_all_text") else None,
            )
            if fragment
        )
        if not content:
            return None

        match = EMAIL_PATTERN.search(unescape(content))
        if match is None:
            return None

        return match.group(0).casefold()

    def _decode_google_redirect(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        if not value.startswith(GOOGLE_REDIRECT_PREFIX):
            return value

        query = parse_qs(urlsplit(value).query)
        target = query.get("q", [None])[0]
        if target is None:
            return None
        return unquote(target)

    def _is_external_url(self, value: str) -> bool:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.netloc:
            return False

        hostname = parsed.netloc.casefold()
        if any(hostname == google_host or hostname.endswith(f".{google_host}") for google_host in GOOGLE_HOSTS):
            return False
        if any(hostname == blocked_host or hostname.endswith(f".{blocked_host}") for blocked_host in NON_WEBSITE_HOSTS):
            return False
        return True

    def _looks_like_phone(self, value: str) -> bool:
        text = value.strip()
        if not PHONE_PATTERN.fullmatch(text):
            return False

        digits = "".join(character for character in text if character.isdigit())
        if len(digits) < 7 or len(digits) > 16:
            return False

        return (
            text.startswith("+")
            or text.startswith("0")
            or digits.startswith("62")
            or any(marker in text for marker in (" ", "-", "(", ")"))
        )

    def _join_address_parts(self, value: Any) -> str | None:
        if not isinstance(value, list):
            return normalize_text(value)

        parts = [part for part in (normalize_text(item) for item in value) if part]
        if not parts:
            return None
        return ", ".join(parts)

    def _walk_strings(self, value: Any) -> list[str]:
        results: list[str] = []
        stack: list[Any] = [value]

        while stack:
            current = stack.pop()
            if isinstance(current, str):
                results.append(current)
                continue
            if isinstance(current, list):
                stack.extend(reversed(current))

        return results

    def _get_list_item(self, value: Any, index: int) -> Any:
        if not isinstance(value, list):
            return None
        if index >= len(value):
            return None
        return value[index]

    def _get_nested_item(self, value: Any, *indices: int) -> Any:
        current = value
        for index in indices:
            current = self._get_list_item(current, index)
            if current is None:
                return None
        return current
