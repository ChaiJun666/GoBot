# GoBot

GoBot is a rewritten lead discovery and campaign intelligence console built with:

- `Python 3.12`
- `uv`
- `FastAPI`
- `Vue 3`
- `Scrapling`
- `SQLite`

The project is in active migration. The older `business-leads-ai-automation` repository is reference logic only. All new implementation lives in this repository.

For Simplified Chinese documentation, see [README_CN.md](README_CN.md).

## Current Status

Implemented today:

- FastAPI backend with SQLite persistence
- Google Maps scraping through Scrapling
- scrape job lifecycle: `queued`, `running`, `completed`, `failed`
- campaign records linked to scrape jobs
- lead intelligence scoring and campaign summary metrics
- Vue 3 console with a workspace layout:
  - `Overview`
  - `Campaigns`
  - `Jobs`
  - `System`
- guided campaign creation drawer
- bilingual UI support for `en` and `zh-CN`
- FastAPI static hosting for the built frontend

Not implemented yet:

- CRM integrations
- outreach automation
- email or WhatsApp content generation
- multi-source scraping beyond Google Maps
- authentication and multi-user separation

## Repository Layout

```text
GoBot/
|-- backend/                  # FastAPI app, domain logic, tests
|-- frontend/                 # Vue 3 + Vite UI
|-- docs/plans/               # implementation plans
|-- .env.example
|-- README.md
`-- README_CN.md
```

Key backend directories:

```text
backend/app/
|-- api/                      # REST routes
|-- core/                     # config, database, job orchestration
|-- schemas/                  # Pydantic models
`-- services/                 # scraping and intelligence services
```

## Architecture

### Backend

The backend currently owns:

- `campaign` creation and retrieval
- linked `scrape_job` execution
- Google Maps scraping through Scrapling
- SQLite persistence for jobs and campaign results
- lead normalization and deduplication
- intelligence scoring and campaign summary metrics
- optional static serving of the built frontend

Important modules:

- [backend/app/main.py](backend/app/main.py)
- [backend/app/api/routes/campaigns.py](backend/app/api/routes/campaigns.py)
- [backend/app/api/routes/scrape_jobs.py](backend/app/api/routes/scrape_jobs.py)
- [backend/app/api/routes/health.py](backend/app/api/routes/health.py)
- [backend/app/core/database.py](backend/app/core/database.py)
- [backend/app/core/job_manager.py](backend/app/core/job_manager.py)
- [backend/app/services/scraping/normalizers.py](backend/app/services/scraping/normalizers.py)
- [backend/app/services/intelligence/scoring.py](backend/app/services/intelligence/scoring.py)

### Frontend

The frontend is now a campaign-first workspace.

- `Overview` shows health and queue summary
- `Campaigns` is the main workbench for campaign queue, selected campaign detail, and scored leads
- `Jobs` is an operations/debugging view for raw jobs and raw results
- `System` shows runtime details
- `New Campaign` opens a drawer instead of keeping a large creation form permanently on screen
- locale switching supports `en` and `zh-CN`, with browser-language detection and persisted preference

Important files:

- [frontend/src/App.vue](frontend/src/App.vue)
- [frontend/src/lib/i18n.ts](frontend/src/lib/i18n.ts)
- [frontend/src/composables/useConsoleWorkspace.ts](frontend/src/composables/useConsoleWorkspace.ts)
- [frontend/src/components/layout/ConsoleShell.vue](frontend/src/components/layout/ConsoleShell.vue)
- [frontend/src/components/campaigns/CampaignCreationDrawer.vue](frontend/src/components/campaigns/CampaignCreationDrawer.vue)
- [frontend/src/components/campaigns/CampaignWorkbench.vue](frontend/src/components/campaigns/CampaignWorkbench.vue)
- [frontend/src/components/jobs/OperationsCenter.vue](frontend/src/components/jobs/OperationsCenter.vue)

## Prerequisites

- Python `3.12`
- Node.js `22+`
- `uv`
- `pnpm`

If your local `uv` cache directory has permission issues, keep using `--no-cache`.

The current scraper does not launch a browser. `playwright` remains in backend dependencies because `Scrapling 0.4.2` imports it internally for compatibility.

## Environment

Copy the example file and adjust values if needed:

```powershell
Copy-Item .env.example .env
```

Supported environment variables:

- `BACKEND_HOST`
- `BACKEND_PORT`
- `SCRAPER_DATABASE_PATH`
- `SCRAPER_TIMEOUT_MS`
- `SCRAPER_VERIFY_TLS`

The SQLite database file is created automatically on first backend startup.

## Development Setup

### 1. Backend

Install backend dependencies:

```powershell
cd backend
uv sync --no-cache
```

Run the backend:

```powershell
uv run --no-cache main.py
```

By default the API runs at `http://127.0.0.1:8000`.

### 2. Frontend

Install frontend dependencies:

```powershell
cd frontend
pnpm.cmd install
```

Start the frontend dev server:

```powershell
pnpm.cmd dev
```

By default Vite runs at `http://127.0.0.1:5173` and proxies `/api` requests to the backend.

## Production-Like Local Run

If you want FastAPI to serve the frontend directly:

1. Build the frontend:

```powershell
cd frontend
pnpm.cmd build
```

2. Start the backend:

```powershell
cd ..\backend
uv run --no-cache main.py
```

Then open:

- `http://127.0.0.1:8000/` for the web UI
- `http://127.0.0.1:8000/docs` for Swagger UI

## API Overview

### Health

- `GET /api/v1/health`

### Campaigns

- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`

### Scrape Jobs

- `POST /api/v1/scrape-jobs`
- `GET /api/v1/scrape-jobs`
- `GET /api/v1/scrape-jobs/{job_id}`
- `GET /api/v1/scrape-jobs/{job_id}/results`

## Example Campaign Request

```json
{
  "name": "Jakarta Coffee Shops",
  "industry": "restaurant",
  "location": "Jakarta",
  "query": "Coffee shops Jakarta Selatan",
  "max_results": 20,
  "source": "google_maps"
}
```

Submitting a campaign will:

1. create a campaign record
2. create a linked scrape job
3. run the scraper asynchronously
4. score the resulting leads
5. store enriched campaign results in SQLite

## Validation

Backend validation:

```powershell
cd backend
python -m compileall .
uv run --no-cache pytest tests/test_health_api.py -v --basetemp=.pytest-tmp
```

Frontend validation:

```powershell
cd frontend
pnpm.cmd test:unit
pnpm.cmd build
```

Current frontend test coverage includes:

- i18n bootstrap and locale resolution
- console workspace state
- console shell rendering
- campaign creation drawer behavior
- campaign workbench rendering
- operations center rendering

## Known Limitations

- Google Maps is still the only scraping source
- Google Maps payload changes may require parser updates
- `SCRAPER_VERIFY_TLS=false` remains the practical default on some Windows setups where `curl_cffi` certificate validation fails
- the UI is bilingual, but not every historical component has been fully localized yet
- there is no authentication or multi-user isolation yet
- the repository is still in migration, so boundaries may continue to evolve
- full backend `pytest` runs can be affected by local Windows temp-directory permissions

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
