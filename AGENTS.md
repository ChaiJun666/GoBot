# GoBot AGENTS

## Project Overview

`GoBot` is the target repository for the rewritten product.

The current migration plan is:

- Keep all new code in this repository
- Use `business-leads-ai-automation` only as a logic reference
- Rebuild the product around:
  - Python `3.12`
  - `uv`
  - `FastAPI`
  - `Vue 3`
  - `Playwright`

At the current stage, only the backend scraping service skeleton is being migrated.

## Current Structure

New migration code should live under:

```text
GoBot/
|-- backend/
|   |-- app/
|   |-- tests/
|   |-- pyproject.toml
|   `-- main.py
|-- .env.example
`-- AGENTS.md
```

## Backend Scope

The backend currently owns:

- scrape job creation and status tracking
- SQLite persistence for jobs and scrape results
- Playwright-based Google Maps scraping
- normalization and deduplication of lead data

The backend should not yet include:

- frontend code
- CRM integrations
- marketing content generation flows
- speculative business logic that has not been confirmed

## Migration Rules

- Treat `business-leads-ai-automation` as a reference, not as the active codebase
- Do not place migrated code outside `E:\\code\\GoBot`
- Preserve stable field concepts from the source logic: `campaign`, `lead`, `intelligence`, and scrape result metadata where relevant
- Prefer minimal, verifiable slices over broad rewrites
- Add tests for normalization, persistence, and other stable backend boundaries first

## Working Rules For Codex

- Read the relevant source behavior before porting it
- Keep backend code modular: API, core, schemas, services
- Keep Playwright logic inside provider/service boundaries
- Keep secrets out of code and out of committed data files
- Avoid introducing extra infrastructure before requirements justify it
