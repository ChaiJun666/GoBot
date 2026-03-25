from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.core.config import Settings
from app.schemas.lead import ScrapedLead
from app.services.scraping.normalizers import deduplicate_leads, normalize_lead
from app.services.scraping.providers.base import ScrapeProvider


class GoogleMapsScrapeProvider(ScrapeProvider):
    source = "google_maps"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def scrape(self, *, query: str, max_results: int) -> list[ScrapedLead]:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright

        search_url = f"https://www.google.com/maps/search/{quote(query)}"

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.settings.scraper_headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(user_agent=self.settings.scraper_user_agent)
            page = await context.new_page()
            page.set_default_timeout(self.settings.scraper_timeout_ms)

            try:
                await page.goto(search_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3_000)
                await self._wait_for_results(page)
                await self._scroll_results(page=page, max_results=max_results)
                raw_results = await page.evaluate(
                    """
                    ({ maxResults }) => {
                      const results = [];
                      const seen = new Set();

                      const normalizeText = (value) => {
                        if (!value) return '';
                        return value.replace(/\\s+/g, ' ').trim();
                      };

                      const looksLikeAddress = (text) => {
                        const lower = text.toLowerCase();
                        return [
                          'jl.', 'jalan', 'street', 'road', 'rd', 'avenue', 'ave',
                          'blok', 'block', 'no.', 'tower', 'plaza', 'mall', 'jakarta',
                          'bandung', 'surabaya', 'bekasi', 'tangerang', 'depok'
                        ].some((token) => lower.includes(token));
                      };

                      const looksLikePhone = (text) => {
                        return /(?:\\+?\\d[\\d\\s().-]{5,})/.test(text);
                      };

                      const extractCard = (card) => {
                        const name = normalizeText(
                          card.querySelector('.qBF1Pd.fontHeadlineSmall')?.textContent
                        );
                        const rating = normalizeText(card.querySelector('.MW4etd')?.textContent);
                        const spans = Array.from(card.querySelectorAll('span'))
                          .map((span) => normalizeText(span.textContent))
                          .filter(Boolean);

                        let address = '';
                        let phone = '';

                        for (const spanText of spans) {
                          if (!address && looksLikeAddress(spanText)) {
                            address = spanText.replace(/^[^\\w+]+/, '');
                            continue;
                          }

                          if (!phone && looksLikePhone(spanText)) {
                            phone = spanText;
                          }
                        }

                        let website = '';
                        let referenceLink = '';
                        const links = Array.from(card.querySelectorAll('a'));
                        for (const link of links) {
                          const href = link.href || '';
                          const text = normalizeText(link.textContent || '');
                          if (!href) continue;

                          if (!referenceLink && href.includes('google.com/maps')) {
                            referenceLink = href;
                          }

                          if (
                            !website &&
                            !href.includes('google.com/maps') &&
                            !href.includes('maps.google.com') &&
                            (
                              href.includes('.com') ||
                              href.includes('.co.id') ||
                              href.includes('.id')
                            )
                          ) {
                            if (!text || text.includes('Website') || text.includes('Situs') || text.includes('www')) {
                              website = href;
                            }
                          }
                        }

                        return {
                          name,
                          address,
                          phone,
                          rating,
                          website,
                          referenceLink,
                          hasWebsite: Boolean(website),
                        };
                      };

                      const pushUnique = (item) => {
                        if (!item?.name || !item?.address) return;
                        const key = `${item.name.toLowerCase()}::${item.address.toLowerCase()}`;
                        if (seen.has(key)) return;
                        seen.add(key);
                        results.push(item);
                      };

                      const separators = document.querySelectorAll('.TFQHme');
                      separators.forEach((separator) => {
                        const nextElement = separator.nextElementSibling;
                        const card = nextElement?.querySelector('.Nv2PK');
                        if (card) {
                          pushUnique(extractCard(card));
                        }
                      });

                      if (results.length === 0) {
                        document.querySelectorAll('.Nv2PK').forEach((card) => {
                          pushUnique(extractCard(card));
                        });
                      }

                      return results.slice(0, maxResults);
                    }
                    """,
                    {"maxResults": max_results},
                )
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(f"Google Maps scrape timed out: {exc}") from exc
            finally:
                await context.close()
                await browser.close()

        normalized = [
            normalized_lead
            for item in raw_results
            if (normalized_lead := normalize_lead(item, source=self.source)) is not None
        ]
        return deduplicate_leads(normalized)[:max_results]

    async def _wait_for_results(self, page: Any) -> None:
        selectors = [".Nv2PK", '[role="feed"]', ".m6QErb"]
        for selector in selectors:
            try:
                await page.locator(selector).first.wait_for(timeout=5_000)
                return
            except Exception:
                continue

    async def _scroll_results(self, *, page: Any, max_results: int) -> None:
        scroll_selectors = [
            '[role="feed"]',
            '.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd',
            '[role="main"]',
        ]

        scroll_target = None
        for selector in scroll_selectors:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                scroll_target = locator
                break

        previous_count = 0
        stagnant_rounds = 0

        for _ in range(self.settings.scraper_max_scroll_attempts):
            current_count = await page.locator(".Nv2PK").count()
            if current_count >= max_results:
                break

            if scroll_target is not None:
                await scroll_target.evaluate("(node) => { node.scrollTop = node.scrollHeight; }")
            else:
                await page.mouse.wheel(0, 2_000)

            await page.wait_for_timeout(self.settings.scraper_scroll_pause_ms)

            next_count = await page.locator(".Nv2PK").count()
            if next_count == previous_count:
                stagnant_rounds += 1
                if stagnant_rounds >= 3:
                    break
            else:
                stagnant_rounds = 0
            previous_count = next_count
