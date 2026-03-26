from __future__ import annotations

import asyncio
import re
from html import unescape
from typing import Any, Mapping
from urllib.parse import quote, urljoin, urlsplit

from scrapling import AsyncFetcher

from app.core.config import Settings
from app.schemas.lead import ScrapedLead
from app.services.scraping.linkedin_session import LinkedInSessionService
from app.services.scraping.normalizers import deduplicate_leads, normalize_lead, normalize_text
from app.services.scraping.providers.base import ScrapeProvider

LINKEDIN_BASE_URL = "https://www.linkedin.com"
LINKEDIN_PROFILE_URL_PATTERN = re.compile(r"https://www\.linkedin\.com/in/[^\"'?#\s<]+|/in/[^\"'?#\s<]+")
LINKEDIN_CARD_PATTERN = re.compile(
    r"<li[^>]*?(?:entity-result|search-result|reusable-search__result-container)[^>]*>(.*?)</li>",
    re.IGNORECASE | re.DOTALL,
)


class LinkedInScrapeProvider(ScrapeProvider):
    source = "linkedin"

    def __init__(self, *, settings: Settings, session_service: LinkedInSessionService) -> None:
        self.settings = settings
        self.session_service = session_service

    async def scrape(
        self,
        *,
        query: str,
        max_results: int,
        query_config: Mapping[str, Any] | None = None,
    ) -> list[ScrapedLead]:
        cookies = self.session_service.require_cookies()
        response = await self._fetch(self._build_search_url(query_config, query), cookies=cookies)
        search_candidates = self._parse_search_results(response.html_content)

        enriched_candidates = await asyncio.gather(
            *(self._hydrate_candidate(candidate, cookies=cookies) for candidate in search_candidates[:max_results]),
        )
        normalized = [
            normalized_lead
            for candidate in enriched_candidates
            if (normalized_lead := normalize_lead(candidate, source=self.source)) is not None
        ]
        return deduplicate_leads(normalized)[:max_results]

    def _build_search_url(self, query_config: Mapping[str, Any] | None, fallback_query: str) -> str:
        if query_config:
            terms = [
                query_config.get("keywords"),
                query_config.get("title"),
                query_config.get("company"),
                query_config.get("location"),
            ]
            search_terms = " ".join(str(term).strip() for term in terms if term)
        else:
            search_terms = fallback_query
        return f"{LINKEDIN_BASE_URL}/search/results/people/?keywords={quote(search_terms)}"

    async def _hydrate_candidate(
        self,
        candidate: dict[str, Any],
        *,
        cookies: dict[str, str],
    ) -> dict[str, Any]:
        profile_url = candidate.get("profile_url")
        if not profile_url:
            return candidate
        try:
            response = await self._fetch(profile_url, cookies=cookies)
        except Exception:
            return candidate
        return {
            **candidate,
            **{
                key: value
                for key, value in self._parse_profile_page(response.html_content, profile_url).items()
                if value and not candidate.get(key)
            },
        }

    async def _fetch(self, url: str, *, cookies: dict[str, str]) -> Any:
        return await AsyncFetcher.get(
            url,
            headers={
                "User-Agent": self.settings.scraper_user_agent,
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=max(self.settings.scraper_timeout_ms / 1000, 1),
            verify=self.settings.scraper_verify_tls,
            cookies=cookies,
            follow_redirects=True,
        )

    def _parse_search_results(self, html: str) -> list[dict[str, Any]]:
        cards = LINKEDIN_CARD_PATTERN.findall(html) or [html]
        results: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for card in cards:
            profile_url = self._extract_profile_url(card)
            if not profile_url or profile_url in seen_urls:
                continue
            seen_urls.add(profile_url)
            text_lines = self._extract_text_lines(card)
            name = self._extract_name(card, text_lines)
            if not name:
                continue
            headline = self._extract_by_marker(card, ("entity-result__primary-subtitle", "subline-level-1"))
            location = self._extract_by_marker(card, ("entity-result__secondary-subtitle", "subline-level-2"))
            results.append(
                {
                    "name": name,
                    "address": location or "LinkedIn profile",
                    "location": location,
                    "headline": headline or self._pick_line(text_lines, exclude={name, location}),
                    "current_company": self._extract_company(headline or ""),
                    "profile_url": profile_url,
                    "reference_link": profile_url,
                }
            )

        return results

    def _parse_profile_page(self, html: str, profile_url: str) -> dict[str, Any]:
        text_lines = self._extract_text_lines(html)
        name = self._extract_meta_content(html, "og:title") or self._extract_h1(html)
        headline = self._extract_by_marker(html, ("text-body-medium", "top-card-layout__headline"))
        location = self._extract_by_marker(html, ("text-body-small", "top-card__subline-item"))
        company = self._extract_company(headline or "") or self._extract_experience_company(text_lines)
        return {
            "name": name,
            "address": location or "LinkedIn profile",
            "location": location,
            "headline": headline,
            "current_company": company,
            "profile_url": profile_url,
            "reference_link": profile_url,
        }

    def _extract_profile_url(self, html: str) -> str | None:
        match = LINKEDIN_PROFILE_URL_PATTERN.search(html)
        if match is None:
            return None
        url = unescape(match.group(0))
        parsed = urlsplit(url)
        if not parsed.scheme:
            return urljoin(LINKEDIN_BASE_URL, url)
        return url

    def _extract_name(self, html: str, lines: list[str]) -> str | None:
        image_alt = self._search_pattern(html, r'alt="([^"]+)"')
        if image_alt:
            return image_alt
        anchor_text = self._search_pattern(
            html,
            r'<a[^>]*href="[^"]*/in/[^"]*"[^>]*>\s*(?:<span[^>]*>)?([^<]+)',
        )
        if anchor_text:
            return anchor_text
        return lines[0] if lines else None

    def _extract_h1(self, html: str) -> str | None:
        return self._search_pattern(html, r"<h1[^>]*>\s*([^<]+)")

    def _extract_meta_content(self, html: str, property_name: str) -> str | None:
        pattern = rf'<meta[^>]+property="{re.escape(property_name)}"[^>]+content="([^"]+)"'
        return self._search_pattern(html, pattern)

    def _extract_experience_company(self, lines: list[str]) -> str | None:
        for index, line in enumerate(lines):
            if line.casefold() == "experience" and index + 1 < len(lines):
                return lines[index + 1]
        return None

    def _extract_company(self, headline: str) -> str | None:
        if " at " in headline:
            _, _, company = headline.partition(" at ")
            return normalize_text(company)
        return None

    def _extract_by_marker(self, html: str, markers: tuple[str, ...]) -> str | None:
        for marker in markers:
            pattern = rf'{re.escape(marker)}[^>]*>\s*<[^>]*>\s*([^<]+)|{re.escape(marker)}[^>]*>\s*([^<]+)'
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return normalize_text(next(group for group in match.groups() if group))
        return None

    def _extract_text_lines(self, html: str) -> list[str]:
        text = re.sub(r"<[^>]+>", "\n", html)
        return [line for line in (normalize_text(unescape(chunk)) for chunk in text.splitlines()) if line]

    def _pick_line(self, lines: list[str], *, exclude: set[str | None]) -> str | None:
        for line in lines:
            if line not in exclude:
                return line
        return None

    def _search_pattern(self, html: str, pattern: str) -> str | None:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match is None:
            return None
        return normalize_text(unescape(match.group(1)))
