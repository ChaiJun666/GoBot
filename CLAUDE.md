# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GoBot is a lead discovery and campaign intelligence console. Despite the name, this is a **Python + Vue.js** monorepo — not Go.

**Stack:** Python 3.12 / FastAPI / SQLite (backend) + Vue 3 / TypeScript / Vite (frontend)

## Commands

### Backend (run from `backend/`)

```powershell
uv sync --no-cache                          # Install dependencies
uv run --no-cache main.py                   # Start server (port 8000)
python -m compileall .                      # Syntax check all .py files
uv run --no-cache pytest tests/ -v          # Run all tests
uv run --no-cache pytest tests/test_health_api.py -v   # Single test file
```

### Frontend (run from `frontend/`)

```powershell
pnpm.cmd install                            # Install dependencies
pnpm.cmd dev                                # Dev server (port 5173, proxies /api to 8000)
pnpm.cmd test:unit                          # Vitest unit tests
pnpm.cmd build                              # Type-check (vue-tsc) + Vite build -> dist/
```

### Production

Build frontend first (`frontend/pnpm.cmd build`), then run backend — FastAPI serves `frontend/dist/` as static files at port 8000.

## Architecture

```
Vue 3 SPA (port 5173)  --/api-->  FastAPI (port 8000)
                                    |
                      +-------------+-------------+
                      |             |             |
                 ScrapeService  JobManager   MailService
                      |           (async)         |
               +------+------+               IMAP/SMTP
               |             |               (10 providers)
          GoogleMaps   LinkedIn           DPAPI crypto
          (Scrapling)  (Scrapling +       (Win32 only)
                        Playwright)

                    LlmConfigService
                         |
                    7 LLM providers
                    (DPAPI crypto)
```

**Data flow for a campaign:**
1. API creates `campaign` + linked `scrape_job` records (status: `queued`)
2. `ScrapeJobManager.enqueue()` spawns an `asyncio.Task`
3. Job lifecycle: `queued` -> `running` -> `completed` | `failed`
4. `ScrapeService.scrape()` dispatches to provider (google_maps or linkedin)
5. Results go through `normalizers.py` (dedup + field normalization)
6. `LeadIntelligenceScorer.score_leads()` applies 6 weighted factors
7. `Database.complete_campaign()` stores enriched leads with summary metrics

**LLM config:** Manages multiple LLM provider configurations (OpenAI, xAI, Anthropic, DeepSeek, Qwen, Zhipu, MiniMax). Only one config can be active at a time. API keys are encrypted via DPAPI. `GET /api/v1/llm/configs/active` returns the active config with decrypted key for runtime use.

**Database:** Raw `sqlite3` — no ORM. Six tables: `scrape_jobs`, `campaigns`, `source_sessions`, `mailboxes`, `mail_messages`, `llm_configs`.

**Frontend:** Single `App.vue` holds all state. No Vue Router — navigation via `useConsoleWorkspace()` composable. 6 workspace views: Overview, Campaigns, Mail, LLM, Jobs, System. Polls every 5s. Bilingual (en + zh-CN) via vue-i18n.

## Key Backend Paths

| Module | Purpose |
|--------|---------|
| `app/main.py` | FastAPI app factory, lifespan, static serving |
| `app/core/config.py` | Pydantic Settings (env vars, `.env` in repo root + backend/) |
| `app/core/crypto.py` | Generic DPAPI `SecretCipher` (used by mail + LLM) |
| `app/core/database.py` | SQLite persistence (all DDL + CRUD) |
| `app/core/job_manager.py` | Async job lifecycle orchestration |
| `app/api/routes/` | REST endpoints: campaigns, scrape_jobs, linkedin, mail, llm, health |
| `app/schemas/` | Pydantic models for all API contracts |
| `app/services/scraping/service.py` | Scrape dispatcher to providers |
| `app/services/scraping/providers/google_maps.py` | Google Maps scraping via Scrapling |
| `app/services/scraping/providers/linkedin.py` | LinkedIn people search scraping |
| `app/services/scraping/linkedin_session.py` | Playwright-based LinkedIn login + cookie extraction |
| `app/services/scraping/normalizers.py` | Lead deduplication and field normalization |
| `app/services/intelligence/scoring.py` | Lead scoring engine (6 weighted factors) |
| `app/services/llm/service.py` | LLM config CRUD + activation + DPAPI key encryption |
| `app/services/mail/service.py` | IMAP sync, SMTP send |

## Key Frontend Paths

| Module | Purpose |
|--------|---------|
| `src/App.vue` | Root component — all state, 6 views, polling |
| `src/types.ts` | TypeScript interfaces (mirrors backend schemas) |
| `src/lib/api.ts` | Fetch-based API client for all endpoints |
| `src/lib/i18n.ts` | vue-i18n setup, locale resolution, persistence |
| `src/composables/useConsoleWorkspace.ts` | Navigation + selection state |
| `src/components/campaigns/` | Campaign creation drawer, workbench, lead table |
| `src/components/llm/LlmConfigWorkspace.vue` | LLM config list + form workspace |
| `src/components/mail/MailWorkspace.vue` | Multi-account email workspace |
| `src/components/system/LinkedInSessionCard.vue` | LinkedIn connection management |

## Platform Constraints

- **Windows-only:** `app/core/crypto.py` uses Windows DPAPI (`CryptProtectData`/`CryptUnprotectData`)
- **TLS:** `SCRAPER_VERIFY_TLS=false` is the practical default on some Windows setups where `curl_cffi` certificate validation fails
- **No authentication** or multi-user isolation is implemented
- **No ORM** — all database access uses raw `sqlite3` with manual SQL
- Use `--no-cache` with `uv` commands if local cache has permission issues
