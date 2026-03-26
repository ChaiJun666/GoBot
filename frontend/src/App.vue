<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useI18n } from "vue-i18n";

import CampaignCreationDrawer from "@/components/campaigns/CampaignCreationDrawer.vue";
import CampaignWorkbench from "@/components/campaigns/CampaignWorkbench.vue";
import CampaignList from "@/components/CampaignList.vue";
import JobList from "@/components/JobList.vue";
import ConsoleShell from "@/components/layout/ConsoleShell.vue";
import OperationsCenter from "@/components/jobs/OperationsCenter.vue";
import MetricCard from "@/components/MetricCard.vue";
import ResultTable from "@/components/ResultTable.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import LinkedInSessionCard from "@/components/system/LinkedInSessionCard.vue";
import { createConsoleWorkspace, type ConsoleView } from "@/composables/useConsoleWorkspace";
import { api } from "@/lib/api";
import { persistLocale, type AppLocale } from "@/lib/i18n";
import { downloadLeadsCsv } from "@/lib/leadExports";
import type {
  CampaignDetail,
  CampaignStatus,
  CampaignSummary,
  ConnectLinkedInSessionRequest,
  CreateCampaignRequest,
  EnrichedLead,
  HealthResponse,
  LinkedInSessionStatus,
  ScrapedLead,
  ScrapeJobResultsResponse,
  ScrapeJobSummary,
} from "@/types";

const campaigns = ref<CampaignSummary[]>([]);
const selectedCampaignDetail = ref<CampaignDetail | null>(null);
const jobs = ref<ScrapeJobSummary[]>([]);
const selectedJobResults = ref<ScrapeJobResultsResponse | null>(null);
const health = ref<HealthResponse | null>(null);
const linkedinSession = ref<LinkedInSessionStatus | null>(null);
const loadingCampaigns = ref(false);
const loadingCampaignDetail = ref(false);
const loadingJobs = ref(false);
const loadingJobResults = ref(false);
const loadingLinkedInSession = ref(false);
const creatingCampaign = ref(false);
const syncingLinkedInSession = ref(false);
const campaignDrawerOpen = ref(false);
const message = ref<string | null>(null);
const campaignFilterQuery = ref("");
const campaignFilterStatus = ref<CampaignStatus | "all">("all");
const retryingCampaignId = ref<string | null>(null);
const retryingJobId = ref<string | null>(null);
const workspace = createConsoleWorkspace({ initialView: "overview" });
const selectedCampaignId = workspace.selectedCampaignId;
const selectedJobId = workspace.selectedJobId;
const activeView = workspace.activeView;

const { locale, t } = useI18n();

let pollTimer: number | null = null;
let pollInFlight = false;

type RefreshMode = "visible" | "silent";

const selectedCampaign = computed(
  () =>
    campaigns.value.find((campaign) => campaign.id === selectedCampaignId.value) ??
    selectedCampaignDetail.value ??
    null,
);

const selectedJob = computed(
  () => jobs.value.find((job) => job.id === selectedJobId.value) ?? selectedJobResults.value?.job ?? null,
);

const linkedJob = computed(
  () => jobs.value.find((job) => job.id === selectedCampaign.value?.job_id) ?? null,
);

const navItems = computed(() => [
  { value: "overview" as ConsoleView, label: t("nav.overview") },
  { value: "campaigns" as ConsoleView, label: t("nav.campaigns") },
  { value: "jobs" as ConsoleView, label: t("nav.jobs") },
  { value: "system" as ConsoleView, label: t("nav.system") },
]);

const localeOptions = [
  { value: "zh-CN" as AppLocale, label: "简中" },
  { value: "en" as AppLocale, label: "EN" },
];

const currentLocale = computed(() => locale.value as AppLocale);
const headerTitle = computed(() => t(`views.${activeView.value}`));
const headerSubtitle = computed(() => t("console.subtitle"));
const filteredCampaigns = computed(() => {
  const needle = campaignFilterQuery.value.trim().toLowerCase();

  return campaigns.value.filter((campaign) => {
    const statusMatches =
      campaignFilterStatus.value === "all" || campaign.status === campaignFilterStatus.value;
    if (!statusMatches) {
      return false;
    }

    if (!needle) {
      return true;
    }

    return [campaign.name, campaign.industry, campaign.location, campaign.query, t(`sources.${campaign.source}`)]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle));
  });
});

const statusCards = computed(() => [
  { label: t("runtime.backend"), value: health.value?.status ?? t("common.unknown") },
  {
    label: t("runtime.database"),
    value: health.value?.database.healthy ? t("common.healthy") : t("common.offline"),
  },
  { label: t("runtime.scraper"), value: health.value?.scraper.engine ?? t("common.unknown") },
]);

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
    return t("overview.metrics.latestActivityEmpty");
  }

  return `${t("overview.metrics.latestActivityPrefix")} ${new Intl.DateTimeFormat("en-GB", {
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

async function refreshLinkedInSession(options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingLinkedInSession.value = true;
  }

  try {
    linkedinSession.value = await api.getLinkedInSession();
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingLinkedInSession.value = false;
    }
  }
}

async function refreshCampaigns(options: { preserveSelection?: boolean; mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingCampaigns.value = true;
  }

  try {
    const payload = await api.listCampaigns();
    campaigns.value = payload;
    workspace.setCampaigns(payload);

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
    if (mode === "visible") {
      loadingCampaigns.value = false;
    }
  }
}

async function refreshJobs(options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingJobs.value = true;
  }

  try {
    jobs.value = await api.listJobs();
    workspace.setJobs(jobs.value);
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingJobs.value = false;
    }
  }
}

async function loadJobResults(jobId: string, options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  const shouldShowLoading = mode === "visible" && selectedJobResults.value?.job.id !== jobId;

  if (shouldShowLoading) {
    loadingJobResults.value = true;
  }

  try {
    selectedJobResults.value = await api.getJobResults(jobId);
  } catch (error) {
    setMessage(error);
  } finally {
    if (shouldShowLoading) {
      loadingJobResults.value = false;
    }
  }
}

async function refreshSelectedCampaign(options: { mode?: RefreshMode } = {}) {
  if (!selectedCampaignId.value) {
    selectedCampaignDetail.value = null;
    return;
  }

  const mode = options.mode ?? "visible";
  const shouldShowLoading =
    mode === "visible" && selectedCampaignDetail.value?.id !== selectedCampaignId.value;

  if (shouldShowLoading) {
    loadingCampaignDetail.value = true;
  }

  try {
    selectedCampaignDetail.value = await api.getCampaign(selectedCampaignId.value);
  } catch (error) {
    setMessage(error);
  } finally {
    if (shouldShowLoading) {
      loadingCampaignDetail.value = false;
    }
  }
}

async function selectJob(jobId: string) {
  workspace.selectJob(jobId);
  await loadJobResults(jobId);
}

async function selectCampaign(campaignId: string) {
  workspace.selectCampaign(campaignId);
  await refreshSelectedCampaign();
}

async function refreshCampaignWorkspace(options: { mode?: RefreshMode } = {}) {
  await refreshCampaigns({ preserveSelection: true, mode: options.mode });
  if (activeView.value === "campaigns") {
    await refreshSelectedCampaign({ mode: options.mode });
  }
}

async function refreshJobsWorkspace(options: { mode?: RefreshMode } = {}) {
  await refreshJobs({ mode: options.mode });
  if (activeView.value === "jobs" && selectedJobId.value) {
    await loadJobResults(selectedJobId.value, { mode: options.mode });
  }
}

async function createCampaign(payload: CreateCampaignRequest) {
  creatingCampaign.value = true;
  try {
    const response = await api.createCampaign(payload);
    message.value = `${t("messages.campaignLaunchedPrefix")} "${response.campaign.name}"`;
    campaignDrawerOpen.value = false;
    await Promise.all([refreshCampaigns(), refreshJobs()]);
    await selectCampaign(response.campaign.id);
  } catch (error) {
    setMessage(error);
  } finally {
    creatingCampaign.value = false;
  }
}

async function connectLinkedInSession(payload: ConnectLinkedInSessionRequest) {
  syncingLinkedInSession.value = true;
  try {
    linkedinSession.value = await api.connectLinkedInSession(payload);
    message.value = t("messages.linkedinConnected");
  } catch (error) {
    setMessage(error);
  } finally {
    syncingLinkedInSession.value = false;
  }
}

async function disconnectLinkedInSession() {
  syncingLinkedInSession.value = true;
  try {
    linkedinSession.value = await api.disconnectLinkedInSession();
    message.value = t("messages.linkedinDisconnected");
  } catch (error) {
    setMessage(error);
  } finally {
    syncingLinkedInSession.value = false;
  }
}

function setMessage(error: unknown) {
  message.value = error instanceof Error ? error.message : t("messages.unexpectedError");
}

function setActiveView(view: ConsoleView) {
  activeView.value = view;
}

function setLocale(nextLocale: AppLocale) {
  locale.value = nextLocale;
  persistLocale(nextLocale, window.localStorage);
}

function openCampaignView() {
  activeView.value = "campaigns";
  campaignDrawerOpen.value = true;
}

function buildExportFilename(prefix: "campaign" | "job", label: string) {
  const safeLabel = label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "leads";
  return `${prefix}-${safeLabel}.csv`;
}

function exportCampaignLeads(leads: EnrichedLead[]) {
  if (!selectedCampaignDetail.value || !leads.length) {
    message.value = t("messages.exportUnavailable");
    return;
  }

  downloadLeadsCsv(buildExportFilename("campaign", selectedCampaignDetail.value.name), leads);
}

function exportJobLeads(leads: ScrapedLead[]) {
  if (!selectedJobResults.value || !leads.length) {
    message.value = t("messages.exportUnavailable");
    return;
  }

  downloadLeadsCsv(buildExportFilename("job", selectedJobResults.value.job.query), leads);
}

async function retryCampaign(campaignId: string) {
  retryingCampaignId.value = campaignId;
  try {
    const retried = await api.retryCampaign(campaignId);
    message.value = `${t("messages.campaignRetryQueued")} "${retried.name}"`;
    await Promise.all([
      refreshCampaignWorkspace({ mode: "silent" }),
      refreshJobsWorkspace({ mode: "silent" }),
    ]);
    if (selectedCampaignId.value === campaignId) {
      await refreshSelectedCampaign({ mode: "silent" });
    }
  } catch (error) {
    setMessage(error);
  } finally {
    retryingCampaignId.value = null;
  }
}

async function retryJob(jobId: string) {
  retryingJobId.value = jobId;
  try {
    const retried = await api.retryJob(jobId);
    message.value = `${t("messages.jobRetryQueued")} ${retried.id.slice(0, 8)}`;
    await Promise.all([
      refreshCampaignWorkspace({ mode: "silent" }),
      refreshJobsWorkspace({ mode: "silent" }),
    ]);
    if (selectedJobId.value === jobId) {
      await loadJobResults(jobId, { mode: "silent" });
    }
  } catch (error) {
    setMessage(error);
  } finally {
    retryingJobId.value = null;
  }
}

async function bootstrap() {
  await Promise.all([refreshHealth(), refreshCampaigns(), refreshJobs(), refreshLinkedInSession()]);
  if (selectedCampaignId.value) {
    await refreshSelectedCampaign();
  }
}

onMounted(async () => {
  await bootstrap();

  pollTimer = window.setInterval(async () => {
    if (pollInFlight) {
      return;
    }

    pollInFlight = true;
    try {
      await Promise.all([
        refreshHealth(),
        refreshCampaignWorkspace({ mode: "silent" }),
        refreshJobsWorkspace({ mode: "silent" }),
        refreshLinkedInSession({ mode: "silent" }),
      ]);
    } finally {
      pollInFlight = false;
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

    <ConsoleShell
      :active-view="activeView"
      :nav-items="navItems"
      :title="headerTitle"
      :subtitle="headerSubtitle"
      :active-locale="currentLocale"
      :locale-options="localeOptions"
      :action-label="t('actions.newCampaign')"
      @select-view="setActiveView"
      @change-locale="setLocale"
      @action="openCampaignView"
    >
      <CampaignCreationDrawer
        :open="campaignDrawerOpen"
        :busy="creatingCampaign"
        :linkedin-connected="Boolean(linkedinSession?.connected)"
        @close="campaignDrawerOpen = false"
        @submit="createCampaign"
      />

      <p v-if="message" class="inline-message global-message">{{ message }}</p>

      <section v-if="activeView === 'overview'" class="view-grid">
        <section class="hero-status">
          <div v-for="card in statusCards" :key="card.label" class="hero-status-card">
            <span class="summary-label">{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
          </div>
        </section>

        <section class="metric-grid">
          <MetricCard :eyebrow="t('overview.metrics.totalCampaigns')" :value="campaigns.length" :detail="activityLabel" />
          <MetricCard
            :eyebrow="t('overview.metrics.priorityLeads')"
            :value="totalPriorityLeads"
            :detail="t('overview.metrics.priorityLeadsDetail')"
          />
          <MetricCard
            :eyebrow="t('overview.metrics.averageScore')"
            :value="averageCampaignScore"
            :detail="t('overview.metrics.averageScoreDetail')"
          />
          <MetricCard
            :eyebrow="t('overview.metrics.inFlight')"
            :value="runningCampaigns"
            :detail="t('overview.metrics.inFlightDetail')"
          />
          <MetricCard
            :eyebrow="t('overview.metrics.leadVolume')"
            :value="totalLeadVolume"
            :detail="t('overview.metrics.leadVolumeDetail')"
          />
          <MetricCard
            :eyebrow="t('overview.metrics.failed')"
            :value="failedCampaigns"
            :detail="t('overview.metrics.failedDetail')"
          />
        </section>

        <section class="panel panel-health">
          <div class="panel-heading">
            <p class="panel-kicker">{{ t("runtime.runtimeKicker") }}</p>
            <h2>{{ t("runtime.serviceHealth") }}</h2>
          </div>

          <dl class="health-grid">
            <div>
              <dt>{{ t("runtime.databasePath") }}</dt>
              <dd>{{ health?.database.path ?? t("common.unknown") }}</dd>
            </div>
            <div>
              <dt>{{ t("runtime.timeout") }}</dt>
              <dd>{{ health?.scraper.timeout_ms ?? 0 }} ms</dd>
            </div>
            <div>
              <dt>{{ t("runtime.tlsVerify") }}</dt>
              <dd>{{ health?.scraper.verify_tls ? t("common.enabled") : t("common.disabled") }}</dd>
            </div>
            <div>
              <dt>{{ t("runtime.polling") }}</dt>
              <dd>5 seconds</dd>
            </div>
          </dl>
        </section>
      </section>

      <section v-else-if="activeView === 'campaigns'" class="view-grid">
        <CampaignList
          :campaigns="filteredCampaigns"
          :selected-campaign-id="selectedCampaignId"
          :loading="loadingCampaigns"
          :filter-query="campaignFilterQuery"
          :filter-status="campaignFilterStatus"
          :total-campaigns="campaigns.length"
          @select="selectCampaign"
          @refresh="refreshCampaignWorkspace()"
          @update-filter-query="campaignFilterQuery = $event"
          @update-filter-status="campaignFilterStatus = $event"
        />

        <CampaignWorkbench
          :campaign="selectedCampaignDetail"
          :linked-job="linkedJob"
          :loading="loadingCampaignDetail"
          :retrying="retryingCampaignId === selectedCampaignDetail?.id"
          @retry="retryCampaign"
          @export="exportCampaignLeads"
        />
      </section>

      <section v-else-if="activeView === 'jobs'" class="view-grid">
        <OperationsCenter>
          <JobList
            :jobs="jobs"
            :selected-job-id="selectedJobId"
            :loading="loadingJobs"
            @select="selectJob"
            @refresh="refreshJobsWorkspace"
          />

          <section class="panel panel-detail">
            <div class="panel-toolbar">
              <div class="panel-heading">
                <p class="panel-kicker">{{ t("jobs.telemetryKicker") }}</p>
                <h2>{{ t("jobs.telemetryTitle") }}</h2>
              </div>
              <StatusBadge v-if="selectedJob" :status="selectedJob.status" />
            </div>
            <dl v-if="selectedJob" class="detail-grid">
              <div>
                <dt>{{ t("campaigns.detail.jobId") }}</dt>
                <dd>{{ selectedJob.id }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.campaignLink") }}</dt>
                <dd>{{ selectedJob.campaign_id ?? t("common.unlinked") }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.created") }}</dt>
                <dd>{{ selectedJob.created_at }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.completed") }}</dt>
                <dd>{{ selectedJob.completed_at ?? t("common.pending") }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.requested") }}</dt>
                <dd>{{ selectedJob.max_results }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.source") }}</dt>
                <dd>{{ t(`sources.${selectedJob.source}`) }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.returned") }}</dt>
                <dd>{{ selectedJob.result_count }}</dd>
              </div>
            </dl>
            <div v-else class="empty-state compact-empty">
              <p>{{ t("common.noJobSelected") }}</p>
              <span>{{ t("jobs.centerDescription") }}</span>
            </div>
          </section>

          <ResultTable
            :payload="selectedJobResults"
            :loading="loadingJobResults"
            :retrying="retryingJobId === selectedJobResults?.job.id"
            @export="exportJobLeads"
            @retry="retryJob"
          />
        </OperationsCenter>
      </section>

      <section v-else class="view-grid">
        <section class="panel panel-health">
          <div class="panel-heading">
            <p class="panel-kicker">{{ t("runtime.runtimeKicker") }}</p>
            <h2>{{ t("runtime.systemDetails") }}</h2>
          </div>

          <dl class="health-grid">
            <div>
              <dt>{{ t("runtime.databasePath") }}</dt>
              <dd>{{ health?.database.path ?? t("common.unknown") }}</dd>
            </div>
            <div>
              <dt>{{ t("runtime.timeout") }}</dt>
              <dd>{{ health?.scraper.timeout_ms ?? 0 }} ms</dd>
            </div>
            <div>
              <dt>{{ t("runtime.tlsVerify") }}</dt>
              <dd>{{ health?.scraper.verify_tls ? t("common.enabled") : t("common.disabled") }}</dd>
            </div>
            <div>
              <dt>{{ t("runtime.selectedCampaign") }}</dt>
              <dd>{{ selectedCampaign?.id?.slice(0, 8) ?? t("common.none") }}</dd>
            </div>
          </dl>
        </section>

        <LinkedInSessionCard
          :session="linkedinSession"
          :busy="loadingLinkedInSession || syncingLinkedInSession"
          @connect="connectLinkedInSession"
          @disconnect="disconnectLinkedInSession"
        />
      </section>
    </ConsoleShell>
  </div>
</template>
