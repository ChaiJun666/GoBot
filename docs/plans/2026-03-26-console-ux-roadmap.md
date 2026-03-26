# Console UX Refresh And Product Iteration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the current GoBot console into a campaign-first workspace that is easier to operate, with built-in Simplified Chinese and English support, while defining a staged product roadmap that fits the current migration scope.

**Architecture:** Keep the existing FastAPI + Vue monorepo split, preserve the current backend campaign/job model, and improve the operator experience primarily through frontend information architecture and state management. Introduce a lightweight frontend i18n layer early so new UI structure and copy land once for both Simplified Chinese and English. Add only the smallest backend contract changes needed for runtime visibility and future filtering so the migration stays verifiable.

**Tech Stack:** Python 3.12, FastAPI, SQLite, Vue 3, TypeScript, Vite, Scrapling, pytest, Vitest, vue-i18n

---

## Assumptions

- Primary user is a single operator or a small internal growth/sales team, not an external self-serve SaaS customer yet.
- Near-term success means: faster campaign launch, clearer processing state, easier lead review, and less exposure to raw telemetry unless debugging.
- Keep `campaign`, `lead`, `intelligence`, and `scrape_job` as stable concepts; do not add CRM or outreach logic in this slice.
- First release of localization supports `zh-CN` and `en` only.
- Backend data remains language-neutral; localization is a frontend presentation concern in this phase.

## Current Feature Inventory

### Backend

- `GET /api/v1/health` runtime health endpoint via [backend/app/api/routes/health.py](E:/code/GoBot/backend/app/api/routes/health.py)
- `POST /api/v1/campaigns`, `GET /api/v1/campaigns`, `GET /api/v1/campaigns/{campaign_id}` via [backend/app/api/routes/campaigns.py](E:/code/GoBot/backend/app/api/routes/campaigns.py)
- `POST /api/v1/scrape-jobs`, `GET /api/v1/scrape-jobs`, `GET /api/v1/scrape-jobs/{job_id}`, `GET /api/v1/scrape-jobs/{job_id}/results` via [backend/app/api/routes/scrape_jobs.py](E:/code/GoBot/backend/app/api/routes/scrape_jobs.py)
- Async job orchestration that moves jobs and campaigns through `queued -> running -> completed/failed` via [backend/app/core/job_manager.py](E:/code/GoBot/backend/app/core/job_manager.py)
- SQLite persistence for jobs, campaigns, and result JSON blobs via [backend/app/core/database.py](E:/code/GoBot/backend/app/core/database.py)
- Lead normalization and deduplication via [backend/app/services/scraping/normalizers.py](E:/code/GoBot/backend/app/services/scraping/normalizers.py)
- Google Maps scraping provider via [backend/app/services/scraping/providers/google_maps.py](E:/code/GoBot/backend/app/services/scraping/providers/google_maps.py)
- Lead intelligence scoring and summary metrics via [backend/app/services/intelligence/scoring.py](E:/code/GoBot/backend/app/services/intelligence/scoring.py)
- Stable backend tests for persistence, normalization, provider parsing, and intelligence scoring under [backend/tests](E:/code/GoBot/backend/tests)

### Frontend

- Single-page dashboard shell in [frontend/src/App.vue](E:/code/GoBot/frontend/src/App.vue)
- Campaign creation form in [frontend/src/components/CampaignComposer.vue](E:/code/GoBot/frontend/src/components/CampaignComposer.vue)
- Campaign queue cards in [frontend/src/components/CampaignList.vue](E:/code/GoBot/frontend/src/components/CampaignList.vue)
- Campaign intelligence lead table in [frontend/src/components/CampaignResults.vue](E:/code/GoBot/frontend/src/components/CampaignResults.vue)
- Raw job queue cards in [frontend/src/components/JobList.vue](E:/code/GoBot/frontend/src/components/JobList.vue)
- Raw job result table in [frontend/src/components/ResultTable.vue](E:/code/GoBot/frontend/src/components/ResultTable.vue)
- Shared API client and domain types in [frontend/src/lib/api.ts](E:/code/GoBot/frontend/src/lib/api.ts) and [frontend/src/types.ts](E:/code/GoBot/frontend/src/types.ts)

## Current Console Problems

- The main screen is a flat dashboard with all modules visible at once in [frontend/src/App.vue](E:/code/GoBot/frontend/src/App.vue#L214). It exposes overview, creation form, queue, detail, telemetry, and raw results simultaneously, which makes the main operator path unclear.
- Campaign workflow and raw job telemetry compete equally for attention. `CampaignList` and `JobList` are both prominent even though jobs are mostly implementation detail for normal users.
- Lead review is buried below several unrelated panels. The most valuable output, the lead table in [frontend/src/components/CampaignResults.vue](E:/code/GoBot/frontend/src/components/CampaignResults.vue#L74), is not the natural focal point after a campaign finishes.
- The creation experience is functional but not guided. [frontend/src/components/CampaignComposer.vue](E:/code/GoBot/frontend/src/components/CampaignComposer.vue) collects fields, but gives no templates, no preview of expected results, and no reassurance around what will happen next.
- There is no clear distinction between operational health and business progress. Runtime data sits next to lead metrics without hierarchy.
- The health contract is inconsistent: frontend expects `scraper.headless` in [frontend/src/types.ts](E:/code/GoBot/frontend/src/types.ts#L105), while backend returns `engine` and `verify_tls` in [backend/app/api/routes/health.py](E:/code/GoBot/backend/app/api/routes/health.py#L20).
- UI copy is currently hard-coded in English across components, which blocks Chinese operators and makes future UX changes more expensive to maintain.
- Card lists use dense metadata rows and the current separators render as garbled `路` characters in [frontend/src/components/CampaignList.vue](E:/code/GoBot/frontend/src/components/CampaignList.vue#L55) and [frontend/src/components/JobList.vue](E:/code/GoBot/frontend/src/components/JobList.vue#L55), which undermines clarity.

## Approach Options

### Option A: Polish The Existing Single Dashboard

- Lowest effort
- Fix labels, spacing, and a few status problems
- Still keeps the user inside one overloaded page

### Option B: Recommended - Campaign Workbench With Secondary Operations Center

- Keep campaigns as the primary object
- Default view becomes `Overview -> Campaigns -> Jobs`
- Jobs move behind an operations view and linked telemetry panel
- Lead inspection becomes the main content area for a selected campaign
- Minimal backend disruption, highest UX gain for current scope

### Option C: Full Multi-Page Product With Routing, Saved Views, CRM Prep

- Strongest long-term foundation
- Too heavy for the current migration stage
- Risks introducing speculative product surface before requirements are confirmed

## Recommended Interaction Model

### Information Architecture

- Left navigation:
  - `Overview`
  - `Campaigns`
  - `Jobs`
  - `System`
- Top workspace bar:
  - current environment health
  - polling freshness
  - language switcher: `简体中文 / EN`
  - quick action button: `New Campaign`
- Default landing view: `Overview`
  - shows health, queue state, recent campaign outcomes, and actions requiring attention

### Campaigns View

- Primary table/list of campaigns with filters: status, industry, search
- Right-side or lower detail workspace for the selected campaign
- Selected campaign shows:
  - summary card
  - execution timeline
  - lead table with filters for priority/category/has website
  - collapsed debug telemetry section
- Empty states guide the user toward creating the first campaign

### New Campaign Flow

- Convert from always-visible form into a drawer or modal opened by `New Campaign`
- Structure the form as:
  - target market
  - search query
  - run size
  - review/launch
- Include presets per industry and copy that explains campaign -> scrape job -> scored leads

### Jobs View

- Treat as an operations/debugging surface
- Show only fields useful for support and diagnosis
- Preserve direct access to raw job results, but keep it out of the default campaign workflow

### Localization Rules

- All operator-facing strings must come from message catalogs, not inline literals inside Vue templates.
- Keep translation keys semantic, for example `campaigns.queue.title`, not component-name-driven keys.
- Store locale files under `frontend/src/locales/en.ts` and `frontend/src/locales/zh-CN.ts`.
- Locale choice should persist in browser storage and default to `zh-CN` when browser language starts with `zh`, otherwise `en`.

## Product Iteration Roadmap

### Phase 0: Console Foundation Cleanup

- Fix runtime contract mismatches
- Introduce testable frontend state management
- Introduce frontend i18n infrastructure and locale toggle
- Reduce visual noise and define one primary user path

### Phase 1: Campaign Workbench

- Add overview screen
- Add campaign filters, better selection persistence, and clearer empty/loading/error states
- Migrate core workspace copy to bilingual message catalogs
- Make leads the main post-run surface

### Phase 2: Actionability

- Add score explanation and factor breakdown
- Add export actions for filtered leads
- Add retry / rerun campaign action for failed or stale runs

### Phase 3: Operational Maturity

- Add backend filtering/pagination for campaigns and jobs
- Add run timeline, warning banners, and recovery affordances
- Add audit-friendly run summaries

### Phase 4: Product Expansion After Current Migration Scope

- CRM handoff
- multi-source scraping
- auth and multi-user separation
- outreach automation only after CRM destination and ownership model are confirmed

## Execution Plan

### Task 1: Fix Runtime Contract And Create A Stable Workspace Model

**Files:**
- Create: `backend/tests/test_health_api.py`
- Modify: `backend/app/api/routes/health.py:10-24`
- Modify: `frontend/src/types.ts:105-114`
- Modify: `frontend/src/lib/api.ts:38-69`
- Test: `backend/tests/test_health_api.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_response_exposes_runtime_fields() -> None:
    client = TestClient(create_app())

    payload = client.get("/api/v1/health").json()

    assert payload["scraper"]["engine"] == "scrapling"
    assert "verify_tls" in payload["scraper"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run --no-cache pytest tests/test_health_api.py -v`
Expected: FAIL because the test file or expected response contract does not exist yet.

**Step 3: Write minimal implementation**

```python
@router.get("/health")
async def healthcheck(request: Request) -> dict[str, object]:
    database = get_database(request)
    settings = request.app.state.settings
    return {
        "status": "ok",
        "database": {
            "path": str(settings.resolved_database_path),
            "healthy": database.healthcheck(),
        },
        "scraper": {
            "engine": "scrapling",
            "timeout_ms": settings.scraper_timeout_ms,
            "verify_tls": settings.scraper_verify_tls,
        },
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run --no-cache pytest tests/test_health_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_health_api.py backend/app/api/routes/health.py frontend/src/types.ts frontend/src/lib/api.ts
git commit -m "fix: align runtime health contract"
```

### Task 2: Add Frontend Test Harness, I18n Foundation, And A Dedicated Workspace Composable

**Files:**
- Create: `frontend/src/lib/i18n.ts`
- Create: `frontend/src/lib/i18n.test.ts`
- Create: `frontend/src/locales/en.ts`
- Create: `frontend/src/locales/zh-CN.ts`
- Create: `frontend/src/composables/useConsoleWorkspace.ts`
- Create: `frontend/src/composables/useConsoleWorkspace.test.ts`
- Create: `frontend/src/test/setup.ts`
- Modify: `frontend/package.json:6-20`
- Modify: `frontend/vite.config.ts:5-26`
- Modify: `frontend/src/main.ts`
- Test: `frontend/src/composables/useConsoleWorkspace.test.ts`
- Test: `frontend/src/lib/i18n.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";

import { createConsoleWorkspace } from "@/composables/useConsoleWorkspace";
import { createI18nOptions } from "@/lib/i18n";

describe("createConsoleWorkspace", () => {
  it("keeps campaign workflow primary and links the selected job", () => {
    const workspace = createConsoleWorkspace({
      campaigns: [{ id: "campaign-1", job_id: "job-1", status: "completed", total_leads: 3 }],
      jobs: [{ id: "job-1", campaign_id: "campaign-1", status: "completed", result_count: 3 }],
    });

    workspace.selectCampaign("campaign-1");

    expect(workspace.activeView.value).toBe("campaigns");
    expect(workspace.linkedJob.value?.id).toBe("job-1");
  });
});

describe("createI18nOptions", () => {
  it("defaults to zh-CN for Chinese browsers", () => {
    expect(createI18nOptions("zh-CN").locale).toBe("zh-CN");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm.cmd exec vitest run src/composables/useConsoleWorkspace.test.ts src/lib/i18n.test.ts`
Expected: FAIL because Vitest, vue-i18n, and the composable/i18n helpers are not configured yet.

**Step 3: Write minimal implementation**

```ts
import { computed, ref } from "vue";

export function createConsoleWorkspace(seed: {
  campaigns: Array<{ id: string; job_id: string; status: string; total_leads: number }>;
  jobs: Array<{ id: string; campaign_id: string | null; status: string; result_count: number }>;
}) {
  const activeView = ref<"overview" | "campaigns" | "jobs" | "system">("campaigns");
  const selectedCampaignId = ref<string | null>(null);

  const linkedJob = computed(() =>
    seed.jobs.find((job) => job.id === seed.campaigns.find((item) => item.id === selectedCampaignId.value)?.job_id) ?? null,
  );

  function selectCampaign(campaignId: string) {
    selectedCampaignId.value = campaignId;
    activeView.value = "campaigns";
  }

  return { activeView, linkedJob, selectCampaign };
}
```

```ts
export function createI18nOptions(language: string | undefined) {
  return {
    locale: language?.startsWith("zh") ? "zh-CN" : "en",
    fallbackLocale: "en",
  };
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm.cmd exec vitest run src/composables/useConsoleWorkspace.test.ts src/lib/i18n.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/src/main.ts frontend/src/test/setup.ts frontend/src/lib/i18n.ts frontend/src/lib/i18n.test.ts frontend/src/locales/en.ts frontend/src/locales/zh-CN.ts frontend/src/composables/useConsoleWorkspace.ts frontend/src/composables/useConsoleWorkspace.test.ts
git commit -m "feat: add console workspace state and i18n foundation"
```

### Task 3: Replace The Flat Dashboard With A Console Shell

**Files:**
- Create: `frontend/src/components/layout/ConsoleShell.vue`
- Create: `frontend/src/components/layout/PrimaryNav.vue`
- Create: `frontend/src/components/layout/WorkspaceHeader.vue`
- Modify: `frontend/src/App.vue:1-383`
- Modify: `frontend/src/style.css:1-348`
- Test: `frontend/src/components/layout/ConsoleShell.test.ts`

**Step 1: Write the failing test**

```ts
import { render, screen } from "@testing-library/vue";
import { describe, expect, it } from "vitest";

import ConsoleShell from "@/components/layout/ConsoleShell.vue";

describe("ConsoleShell", () => {
  it("renders overview, campaigns, jobs, and system navigation", () => {
    render(ConsoleShell, { props: { activeView: "overview" } });

    expect(screen.getByRole("navigation")).toBeTruthy();
    expect(screen.getByText("Overview")).toBeTruthy();
    expect(screen.getByText("Campaigns")).toBeTruthy();
    expect(screen.getByText("Jobs")).toBeTruthy();
    expect(screen.getByText("System")).toBeTruthy();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/layout/ConsoleShell.test.ts`
Expected: FAIL because the shell component does not exist yet.

**Step 3: Write minimal implementation**

```vue
<script setup lang="ts">
defineProps<{ activeView: "overview" | "campaigns" | "jobs" | "system" }>();
</script>

<template>
  <div class="console-shell">
    <nav class="primary-nav" aria-label="Primary">
      <button>{{ $t("nav.overview") }}</button>
      <button>{{ $t("nav.campaigns") }}</button>
      <button>{{ $t("nav.jobs") }}</button>
      <button>{{ $t("nav.system") }}</button>
    </nav>
    <main class="workspace-content">
      <slot />
    </main>
  </div>
</template>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/layout/ConsoleShell.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/style.css frontend/src/components/layout/ConsoleShell.vue frontend/src/components/layout/PrimaryNav.vue frontend/src/components/layout/WorkspaceHeader.vue frontend/src/components/layout/ConsoleShell.test.ts
git commit -m "feat: introduce console shell layout"
```

### Task 4: Turn Campaign Creation Into A Guided Drawer

**Files:**
- Create: `frontend/src/components/campaigns/CampaignCreationDrawer.vue`
- Create: `frontend/src/components/campaigns/CampaignCreationDrawer.test.ts`
- Modify: `frontend/src/App.vue:214-381`
- Modify: `frontend/src/types.ts:68-103`
- Test: `frontend/src/components/campaigns/CampaignCreationDrawer.test.ts`

**Step 1: Write the failing test**

```ts
import { fireEvent, render, screen } from "@testing-library/vue";
import { describe, expect, it } from "vitest";

import CampaignCreationDrawer from "@/components/campaigns/CampaignCreationDrawer.vue";

describe("CampaignCreationDrawer", () => {
  it("disables launch until required fields are filled", async () => {
    render(CampaignCreationDrawer, { props: { open: true, busy: false } });

    expect(screen.getByRole("button", { name: /launch campaign/i })).toBeDisabled();

    await fireEvent.update(screen.getByLabelText("Campaign name"), "Jakarta coffee");
    await fireEvent.update(screen.getByLabelText("Search query"), "Coffee shops Jakarta");

    expect(screen.getByRole("button", { name: /launch campaign/i })).not.toBeDisabled();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/campaigns/CampaignCreationDrawer.test.ts`
Expected: FAIL because the new drawer component does not exist yet.

**Step 3: Write minimal implementation**

```vue
<script setup lang="ts">
import { computed, reactive } from "vue";

const props = defineProps<{ open: boolean; busy: boolean }>();
const emit = defineEmits<{ submit: [payload: { name: string; query: string; industry: string; location: string; max_results: number; source: "google_maps" }] }>();

const form = reactive({
  name: "",
  industry: "professional",
  location: "",
  query: "",
  max_results: 20,
  source: "google_maps" as const,
});

const canSubmit = computed(() => form.name.trim() && form.query.trim() && !props.busy);
</script>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/campaigns/CampaignCreationDrawer.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/types.ts frontend/src/components/campaigns/CampaignCreationDrawer.vue frontend/src/components/campaigns/CampaignCreationDrawer.test.ts
git commit -m "feat: add guided campaign creation drawer"
```

### Task 5: Build The Campaign Workbench Around Lead Review

**Files:**
- Create: `frontend/src/components/campaigns/CampaignWorkbench.vue`
- Create: `frontend/src/components/campaigns/CampaignQueueTable.vue`
- Create: `frontend/src/components/campaigns/LeadInspectorTable.vue`
- Create: `frontend/src/components/campaigns/CampaignWorkbench.test.ts`
- Modify: `frontend/src/App.vue:246-380`
- Modify: `frontend/src/components/CampaignList.vue:30-75`
- Modify: `frontend/src/components/CampaignResults.vue:39-115`
- Test: `frontend/src/components/campaigns/CampaignWorkbench.test.ts`

**Step 1: Write the failing test**

```ts
import { render, screen } from "@testing-library/vue";
import { describe, expect, it } from "vitest";

import CampaignWorkbench from "@/components/campaigns/CampaignWorkbench.vue";

describe("CampaignWorkbench", () => {
  it("shows selected campaign summary before telemetry", () => {
    render(CampaignWorkbench, {
      props: {
        campaign: { id: "campaign-1", name: "Jakarta coffee", status: "completed", priority_leads: 2, average_score: 84, results: [] },
        linkedJob: { id: "job-1", status: "completed", result_count: 5 },
      },
    });

    expect(screen.getByText("Selected campaign")).toBeTruthy();
    expect(screen.getByText("Lead review")).toBeTruthy();
    expect(screen.getByText("Execution telemetry")).toBeTruthy();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/campaigns/CampaignWorkbench.test.ts`
Expected: FAIL because the workbench component does not exist yet.

**Step 3: Write minimal implementation**

```vue
<template>
  <section class="campaign-workbench">
    <header class="workbench-summary">
      <h2>Selected campaign</h2>
      <p>Lead review</p>
    </header>
    <section class="lead-review">
      <slot name="leads" />
    </section>
    <details class="telemetry-panel">
      <summary>Execution telemetry</summary>
      <slot name="telemetry" />
    </details>
  </section>
</template>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/campaigns/CampaignWorkbench.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/CampaignList.vue frontend/src/components/CampaignResults.vue frontend/src/components/campaigns/CampaignWorkbench.vue frontend/src/components/campaigns/CampaignQueueTable.vue frontend/src/components/campaigns/LeadInspectorTable.vue frontend/src/components/campaigns/CampaignWorkbench.test.ts
git commit -m "feat: center campaign workbench on lead review"
```

### Task 6: Move Raw Jobs Into A Secondary Operations View

**Files:**
- Create: `frontend/src/components/jobs/OperationsCenter.vue`
- Create: `frontend/src/components/jobs/OperationsCenter.test.ts`
- Modify: `frontend/src/App.vue:332-380`
- Modify: `frontend/src/components/JobList.vue:30-68`
- Modify: `frontend/src/components/ResultTable.vue:44-112`
- Test: `frontend/src/components/jobs/OperationsCenter.test.ts`

**Step 1: Write the failing test**

```ts
import { render, screen } from "@testing-library/vue";
import { describe, expect, it } from "vitest";

import OperationsCenter from "@/components/jobs/OperationsCenter.vue";

describe("OperationsCenter", () => {
  it("keeps raw jobs behind an explicit operations heading", () => {
    render(OperationsCenter, { props: { jobs: [], selectedJobId: null, loading: false } });

    expect(screen.getByText("Operations center")).toBeTruthy();
    expect(screen.getByText("Raw jobs and results")).toBeTruthy();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/jobs/OperationsCenter.test.ts`
Expected: FAIL because the component does not exist yet.

**Step 3: Write minimal implementation**

```vue
<template>
  <section class="operations-center">
    <header>
      <h2>Operations center</h2>
      <p>Raw jobs and results</p>
    </header>
    <slot />
  </section>
</template>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm.cmd exec vitest run src/components/jobs/OperationsCenter.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/JobList.vue frontend/src/components/ResultTable.vue frontend/src/components/jobs/OperationsCenter.vue frontend/src/components/jobs/OperationsCenter.test.ts
git commit -m "feat: move raw jobs into operations center"
```

### Task 7: Verify The New Console Flow And Update Project Docs

**Files:**
- Modify: `README.md:11-171`
- Modify: `README_CN.md:11-176`
- Test: `backend/tests/test_health_api.py`
- Test: `frontend/src/composables/useConsoleWorkspace.test.ts`
- Test: `frontend/src/components/layout/ConsoleShell.test.ts`
- Test: `frontend/src/components/campaigns/CampaignCreationDrawer.test.ts`
- Test: `frontend/src/components/campaigns/CampaignWorkbench.test.ts`
- Test: `frontend/src/components/jobs/OperationsCenter.test.ts`

**Step 1: Write the failing test**

```md
- Console entry point should mention Overview, Campaigns, Jobs, and System
- Campaign creation should be described as a guided flow
- Jobs should be documented as an operations/debugging view
- Documentation should mention Simplified Chinese and English locale support
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm.cmd build`
Expected: FAIL or reveal unresolved imports/typing gaps until all redesign components are wired together.

**Step 3: Write minimal implementation**

```md
## Frontend

The frontend now uses a workspace layout:

- Overview for system and queue summary
- Campaigns for the primary operating flow
- Jobs for raw execution debugging
- System for runtime visibility
- Locale support for `zh-CN` and `en`
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run --no-cache pytest -v`
Expected: PASS

Run: `cd frontend && pnpm.cmd exec vitest run`
Expected: PASS

Run: `cd frontend && pnpm.cmd build`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md README_CN.md backend/tests/test_health_api.py frontend/src
git commit -m "docs: describe campaign-first console workflow"
```

## Notes For The Implementer

- Do not add Vue Router unless the shell becomes hard to manage without it. Keep navigation state local first.
- Do not invent CRM, outreach, or analytics objects in this phase.
- Keep jobs accessible, but visually secondary.
- Keep all new UI strings behind i18n keys from the first component change onward.
- Use `@brainstorming` decisions above as the design source of truth.
- Keep tests focused on state boundaries and operator-visible behavior, not pixel snapshots.
