# GoBot

GoBot is a rewritten lead discovery and campaign intelligence console built with:

- `Python 3.12`
- `uv`
- `FastAPI`
- `Vue 3`
- `Scrapling`
- `SQLite`

The project is currently in active migration. It uses the older `business-leads-ai-automation` repository as a logic reference only, while all new implementation lives inside this repository.

For Chinese documentation, see [README_CN.md](README_CN.md).

## Current Status

What is already implemented:

- FastAPI backend with SQLite persistence
- Scrapling-based Google Maps scraping provider
- scrape job lifecycle: queued, running, completed, failed
- campaign domain model linked to scrape jobs
- lead intelligence scoring for campaign results
- Vue 3 frontend console for:
  - launching campaigns
  - browsing campaign queue
  - inspecting intelligence-scored leads
  - checking raw execution jobs and health status
- FastAPI static hosting for the built frontend

What is not implemented yet:

- CRM integrations
- outreach automation
- email or WhatsApp content generation
- multi-source scraping beyond Google Maps
- advanced analytics beyond current campaign/job views

## Repository Layout

```text
GoBot/
|-- backend/                  # FastAPI app, domain logic, tests
|-- frontend/                 # Vue 3 + Vite UI
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

The backend owns:

- `campaign` creation and retrieval
- linked `scrape_job` execution
- Google Maps scraping through Scrapling
- SQLite persistence for jobs and campaign results
- intelligence scoring and campaign summary metrics
- optional static serving of the built frontend

Important modules:

- [backend/app/main.py](backend/app/main.py)
- [backend/app/api/routes/campaigns.py](backend/app/api/routes/campaigns.py)
- [backend/app/api/routes/scrape_jobs.py](backend/app/api/routes/scrape_jobs.py)
- [backend/app/core/database.py](backend/app/core/database.py)
- [backend/app/core/job_manager.py](backend/app/core/job_manager.py)
- [backend/app/services/scraping/providers/google_maps.py](backend/app/services/scraping/providers/google_maps.py)
- [backend/app/services/intelligence/scoring.py](backend/app/services/intelligence/scoring.py)

### Frontend

The frontend is a campaign-first control panel. It treats campaigns as the main workflow and keeps raw scrape jobs visible as execution telemetry.

Main screens include:

- campaign launch form
- campaign queue
- campaign intelligence result table
- linked scrape job telemetry
- backend health card

Important files:

- [frontend/src/App.vue](frontend/src/App.vue)
- [frontend/src/components/CampaignComposer.vue](frontend/src/components/CampaignComposer.vue)
- [frontend/src/components/CampaignList.vue](frontend/src/components/CampaignList.vue)
- [frontend/src/components/CampaignResults.vue](frontend/src/components/CampaignResults.vue)
- [frontend/src/lib/api.ts](frontend/src/lib/api.ts)

## Prerequisites

- Python `3.12`
- Node.js `22+`
- `uv`
- `pnpm`

If your local `uv` cache directory has permission issues, keep using `--no-cache` in `uv` commands.

The current scraper does not launch a browser. The `playwright` Python package remains in backend dependencies only because `Scrapling 0.4.2` imports it internally for compatibility.

## Environment

Copy the example file and adjust values if needed:

```powershell
Copy-Item .env.example .env
```

Current environment variables:

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

By default the Vite dev server runs at `http://127.0.0.1:5173` and proxies `/api` requests to the backend.

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

Current API surface:

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
```

Frontend validation:

```powershell
cd frontend
pnpm.cmd exec vue-tsc --noEmit
pnpm.cmd build
```

Backend tests currently exist for:

- database persistence
- lead normalization
- intelligence scoring

## Known Limitations

- The scraper currently supports Google Maps only
- Google Maps payload structure may need adjustment if Google changes the internal response format
- `SCRAPER_VERIFY_TLS=false` is the practical default on some Windows setups where `curl_cffi` certificate validation fails
- The frontend currently focuses on campaigns and execution telemetry, not full business analytics
- There is no authentication or multi-user separation yet
- The project is still in migration, so naming and boundaries may continue to evolve

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
