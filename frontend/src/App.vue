<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import CampaignComposer from "@/components/CampaignComposer.vue";
import CampaignList from "@/components/CampaignList.vue";
import CampaignResults from "@/components/CampaignResults.vue";
import JobList from "@/components/JobList.vue";
import MetricCard from "@/components/MetricCard.vue";
import ResultTable from "@/components/ResultTable.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { api } from "@/lib/api";
import type {
  CampaignDetail,
  CampaignSummary,
  CreateCampaignRequest,
  HealthResponse,
  ScrapeJobResultsResponse,
  ScrapeJobSummary,
} from "@/types";

const campaigns = ref<CampaignSummary[]>([]);
const selectedCampaignId = ref<string | null>(null);
const selectedCampaignDetail = ref<CampaignDetail | null>(null);
const jobs = ref<ScrapeJobSummary[]>([]);
const selectedJobId = ref<string | null>(null);
const selectedJobResults = ref<ScrapeJobResultsResponse | null>(null);
const health = ref<HealthResponse | null>(null);
const loadingCampaigns = ref(false);
const loadingCampaignDetail = ref(false);
const loadingJobs = ref(false);
const loadingJobResults = ref(false);
const creatingCampaign = ref(false);
const message = ref<string | null>(null);

let pollTimer: number | null = null;

const selectedCampaign = computed(
  () =>
    campaigns.value.find((campaign) => campaign.id === selectedCampaignId.value) ??
    selectedCampaignDetail.value ??
    null,
);

const linkedJob = computed(
  () => jobs.value.find((job) => job.id === selectedCampaign.value?.job_id) ?? null,
);

const totalLeadVolume = computed(() =>
  campaigns.value.reduce((sum, campaign) => sum + campaign.total_leads, 0),
);

const averageCampaignScore = computed(() => {
  const completed = campaigns.value.filter((campaign) => campaign.total_leads > 0);
  if (!completed.length) {
    return 0;
  }
  return Math.round(
    completed.reduce((sum, campaign) => sum + campaign.average_score, 0) / completed.length,
  );
});

const runningCampaigns = computed(
  () =>
    campaigns.value.filter(
      (campaign) => campaign.status === "queued" || campaign.status === "running",
    ).length,
);

const failedCampaigns = computed(
  () => campaigns.value.filter((campaign) => campaign.status === "failed").length,
);

const totalPriorityLeads = computed(() =>
  campaigns.value.reduce((sum, campaign) => sum + campaign.priority_leads, 0),
);

const activityLabel = computed(() => {
  const latest = campaigns.value[0];
  if (!latest) {
    return "No campaign activity yet";
  }

  return `Latest update ${new Intl.DateTimeFormat("en-GB", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(latest.updated_at))}`;
});

async function refreshHealth() {
  try {
    health.value = await api.getHealth();
  } catch (error) {
    setMessage(error);
  }
}

async function refreshCampaigns(options: { preserveSelection?: boolean } = {}) {
  loadingCampaigns.value = true;
  try {
    const payload = await api.listCampaigns();
    campaigns.value = payload;

    if (!payload.length) {
      selectedCampaignId.value = null;
      selectedCampaignDetail.value = null;
      selectedJobId.value = null;
      selectedJobResults.value = null;
      return;
    }

    if (!options.preserveSelection || !selectedCampaignId.value) {
      selectedCampaignId.value = payload[0].id;
    }

    if (!payload.some((campaign) => campaign.id === selectedCampaignId.value)) {
      selectedCampaignId.value = payload[0].id;
    }
  } catch (error) {
    setMessage(error);
  } finally {
    loadingCampaigns.value = false;
  }
}

async function refreshJobs() {
  loadingJobs.value = true;
  try {
    jobs.value = await api.listJobs();
  } catch (error) {
    setMessage(error);
  } finally {
    loadingJobs.value = false;
  }
}

async function selectJob(jobId: string) {
  selectedJobId.value = jobId;
  loadingJobResults.value = true;
  try {
    selectedJobResults.value = await api.getJobResults(jobId);
  } catch (error) {
    setMessage(error);
  } finally {
    loadingJobResults.value = false;
  }
}

async function selectCampaign(campaignId: string) {
  selectedCampaignId.value = campaignId;
  loadingCampaignDetail.value = true;
  try {
    selectedCampaignDetail.value = await api.getCampaign(campaignId);
    const jobId = selectedCampaignDetail.value.job_id;
    if (jobId) {
      await selectJob(jobId);
    }
  } catch (error) {
    setMessage(error);
  } finally {
    loadingCampaignDetail.value = false;
  }
}

async function createCampaign(payload: CreateCampaignRequest) {
  creatingCampaign.value = true;
  try {
    const response = await api.createCampaign(payload);
    message.value = `Launched campaign "${response.campaign.name}"`;
    await Promise.all([refreshCampaigns(), refreshJobs()]);
    await selectCampaign(response.campaign.id);
  } catch (error) {
    setMessage(error);
  } finally {
    creatingCampaign.value = false;
  }
}

function setMessage(error: unknown) {
  message.value = error instanceof Error ? error.message : "Unexpected error";
}

async function bootstrap() {
  await Promise.all([refreshHealth(), refreshCampaigns(), refreshJobs()]);
  if (selectedCampaignId.value) {
    await selectCampaign(selectedCampaignId.value);
  }
}

onMounted(async () => {
  await bootstrap();

  pollTimer = window.setInterval(async () => {
    await Promise.all([
      refreshHealth(),
      refreshCampaigns({ preserveSelection: true }),
      refreshJobs(),
    ]);

    if (selectedCampaignId.value) {
      await selectCampaign(selectedCampaignId.value);
    }
  }, 5000);
});

onUnmounted(() => {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
  }
});
</script>

<template>
  <div class="app-shell">
    <div class="background-orbit background-orbit-a"></div>
    <div class="background-orbit background-orbit-b"></div>

    <header class="hero">
      <div>
        <p class="hero-kicker">GoBot Console</p>
        <h1>Run campaigns, score leads, inspect execution.</h1>
        <p class="hero-copy">
          The console now treats campaigns as the primary workflow. Each campaign launches
          a scrape job, waits for lead extraction, then calculates intelligence scores so
          you can inspect qualified prospects in one place.
        </p>
      </div>

      <div class="hero-status">
        <div class="hero-status-card">
          <span class="summary-label">Backend</span>
          <strong>{{ health?.status ?? "unknown" }}</strong>
        </div>
        <div class="hero-status-card">
          <span class="summary-label">Database</span>
          <strong>{{ health?.database.healthy ? "healthy" : "offline" }}</strong>
        </div>
        <div class="hero-status-card">
          <span class="summary-label">Mode</span>
          <strong>{{ health?.scraper.headless ? "headless" : "headed" }}</strong>
        </div>
      </div>
    </header>

    <main class="dashboard-grid">
      <section class="metric-grid">
        <MetricCard eyebrow="Total campaigns" :value="campaigns.length" :detail="activityLabel" />
        <MetricCard eyebrow="Priority leads" :value="totalPriorityLeads" detail="High-value prospects found" />
        <MetricCard eyebrow="Average score" :value="averageCampaignScore" detail="Across completed campaigns" />
        <MetricCard eyebrow="In flight" :value="runningCampaigns" detail="Queued or actively processing" />
        <MetricCard eyebrow="Lead volume" :value="totalLeadVolume" detail="All intelligence-scored leads" />
        <MetricCard eyebrow="Failed" :value="failedCampaigns" detail="Campaigns needing review" />
      </section>

      <CampaignComposer :busy="creatingCampaign" @submit="createCampaign" />

      <section class="panel panel-health">
        <div class="panel-heading">
          <p class="panel-kicker">Runtime</p>
          <h2>Service health</h2>
        </div>

        <dl class="health-grid">
          <div>
            <dt>Database path</dt>
            <dd>{{ health?.database.path ?? "unavailable" }}</dd>
          </div>
          <div>
            <dt>Timeout</dt>
            <dd>{{ health?.scraper.timeout_ms ?? 0 }} ms</dd>
          </div>
          <div>
            <dt>Polling</dt>
            <dd>5 seconds</dd>
          </div>
          <div>
            <dt>Selected campaign</dt>
            <dd>{{ selectedCampaign?.id?.slice(0, 8) ?? "none" }}</dd>
          </div>
        </dl>

        <p v-if="message" class="inline-message">{{ message }}</p>
      </section>

      <CampaignList
        :campaigns="campaigns"
        :selected-campaign-id="selectedCampaignId"
        :loading="loadingCampaigns"
        @select="selectCampaign"
        @refresh="refreshCampaigns({ preserveSelection: true })"
      />

      <CampaignResults :campaign="selectedCampaignDetail" :loading="loadingCampaignDetail" />

      <section v-if="selectedCampaign" class="panel panel-detail">
        <div class="panel-toolbar">
          <div class="panel-heading">
            <p class="panel-kicker">Selected</p>
            <h2>Campaign detail</h2>
          </div>
          <StatusBadge :status="selectedCampaign.status" />
        </div>
        <dl class="detail-grid">
          <div>
            <dt>Name</dt>
            <dd>{{ selectedCampaign.name }}</dd>
          </div>
          <div>
            <dt>Industry</dt>
            <dd>{{ selectedCampaign.industry }}</dd>
          </div>
          <div>
            <dt>Location</dt>
            <dd>{{ selectedCampaign.location }}</dd>
          </div>
          <div>
            <dt>Query</dt>
            <dd>{{ selectedCampaign.query }}</dd>
          </div>
          <div>
            <dt>Job id</dt>
            <dd>{{ selectedCampaign.job_id }}</dd>
          </div>
          <div>
            <dt>Leads</dt>
            <dd>{{ selectedCampaign.total_leads }}</dd>
          </div>
        </dl>
      </section>

      <JobList
        :jobs="jobs"
        :selected-job-id="selectedJobId"
        :loading="loadingJobs"
        @select="selectJob"
        @refresh="refreshJobs"
      />

      <section class="panel panel-detail">
        <div class="panel-toolbar">
          <div class="panel-heading">
            <p class="panel-kicker">Telemetry</p>
            <h2>Linked execution job</h2>
          </div>
          <StatusBadge v-if="linkedJob" :status="linkedJob.status" />
        </div>
        <dl v-if="linkedJob" class="detail-grid">
          <div>
            <dt>Job id</dt>
            <dd>{{ linkedJob.id }}</dd>
          </div>
          <div>
            <dt>Campaign link</dt>
            <dd>{{ linkedJob.campaign_id ?? "unlinked" }}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{{ linkedJob.created_at }}</dd>
          </div>
          <div>
            <dt>Completed</dt>
            <dd>{{ linkedJob.completed_at ?? "Pending" }}</dd>
          </div>
          <div>
            <dt>Requested</dt>
            <dd>{{ linkedJob.max_results }}</dd>
          </div>
          <div>
            <dt>Returned</dt>
            <dd>{{ linkedJob.result_count }}</dd>
          </div>
        </dl>
        <div v-else class="empty-state compact-empty">
          <p>No linked job selected.</p>
          <span>Select a campaign or raw job to inspect execution details.</span>
        </div>
      </section>

      <ResultTable :payload="selectedJobResults" :loading="loadingJobResults" />
    </main>
  </div>
</template>
