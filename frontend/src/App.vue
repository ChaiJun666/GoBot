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
import { createConsoleWorkspace, type ConsoleView } from "@/composables/useConsoleWorkspace";
import { api } from "@/lib/api";
import { persistLocale, type AppLocale } from "@/lib/i18n";
import type {
  CampaignDetail,
  CampaignSummary,
  CreateCampaignRequest,
  HealthResponse,
  ScrapeJobResultsResponse,
  ScrapeJobSummary,
} from "@/types";

const campaigns = ref<CampaignSummary[]>([]);
const selectedCampaignDetail = ref<CampaignDetail | null>(null);
const jobs = ref<ScrapeJobSummary[]>([]);
const selectedJobResults = ref<ScrapeJobResultsResponse | null>(null);
const health = ref<HealthResponse | null>(null);
const loadingCampaigns = ref(false);
const loadingCampaignDetail = ref(false);
const loadingJobs = ref(false);
const loadingJobResults = ref(false);
const creatingCampaign = ref(false);
const campaignDrawerOpen = ref(false);
const message = ref<string | null>(null);
const workspace = createConsoleWorkspace({ initialView: "overview" });
const selectedCampaignId = workspace.selectedCampaignId;
const selectedJobId = workspace.selectedJobId;
const activeView = workspace.activeView;

const { locale, t } = useI18n();

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

const navItems = computed(() => [
  { value: "overview" as ConsoleView, label: t("nav.overview") },
  { value: "campaigns" as ConsoleView, label: t("nav.campaigns") },
  { value: "jobs" as ConsoleView, label: t("nav.jobs") },
  { value: "system" as ConsoleView, label: t("nav.system") },
]);

const localeOptions = [
  { value: "zh-CN" as AppLocale, label: "简体中文" },
  { value: "en" as AppLocale, label: "EN" },
];

const currentLocale = computed(() => locale.value as AppLocale);
const headerTitle = computed(() => t(`views.${activeView.value}`));
const headerSubtitle = computed(() => t("console.subtitle"));

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

async function refreshCampaigns(options: { preserveSelection?: boolean } = {}) {
  loadingCampaigns.value = true;
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
    loadingCampaigns.value = false;
  }
}

async function refreshJobs() {
  loadingJobs.value = true;
  try {
    jobs.value = await api.listJobs();
    workspace.setJobs(jobs.value);
  } catch (error) {
    setMessage(error);
  } finally {
    loadingJobs.value = false;
  }
}

async function selectJob(jobId: string) {
  workspace.selectJob(jobId);
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
  workspace.selectCampaign(campaignId);
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
        @close="campaignDrawerOpen = false"
        @submit="createCampaign"
      />

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

          <p v-if="message" class="inline-message">{{ message }}</p>
        </section>
      </section>

      <section v-else-if="activeView === 'campaigns'" class="view-grid">
        <CampaignList
          :campaigns="campaigns"
          :selected-campaign-id="selectedCampaignId"
          :loading="loadingCampaigns"
          @select="selectCampaign"
          @refresh="refreshCampaigns({ preserveSelection: true })"
        />

        <CampaignWorkbench
          :campaign="selectedCampaignDetail"
          :linked-job="linkedJob"
          :loading="loadingCampaignDetail"
        />
      </section>

      <section v-else-if="activeView === 'jobs'" class="view-grid">
        <OperationsCenter>
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
                <p class="panel-kicker">{{ t("jobs.telemetryKicker") }}</p>
                <h2>{{ t("jobs.telemetryTitle") }}</h2>
              </div>
              <StatusBadge v-if="linkedJob" :status="linkedJob.status" />
            </div>
            <dl v-if="linkedJob" class="detail-grid">
              <div>
                <dt>{{ t("campaigns.detail.jobId") }}</dt>
                <dd>{{ linkedJob.id }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.campaignLink") }}</dt>
                <dd>{{ linkedJob.campaign_id ?? t("common.unlinked") }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.created") }}</dt>
                <dd>{{ linkedJob.created_at }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.completed") }}</dt>
                <dd>{{ linkedJob.completed_at ?? t("common.pending") }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.requested") }}</dt>
                <dd>{{ linkedJob.max_results }}</dd>
              </div>
              <div>
                <dt>{{ t("jobs.returned") }}</dt>
                <dd>{{ linkedJob.result_count }}</dd>
              </div>
            </dl>
            <div v-else class="empty-state compact-empty">
              <p>{{ t("common.noLinkedJobSelected") }}</p>
              <span>{{ t("campaigns.telemetryEmptyDescription") }}</span>
            </div>
          </section>

          <ResultTable :payload="selectedJobResults" :loading="loadingJobResults" />
        </OperationsCenter>
      </section>

      <section v-else class="view-grid">
        <section class="hero-status">
          <div v-for="card in statusCards" :key="card.label" class="hero-status-card">
            <span class="summary-label">{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
          </div>
        </section>

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

          <p v-if="message" class="inline-message">{{ message }}</p>
        </section>
      </section>
    </ConsoleShell>
  </div>
</template>
