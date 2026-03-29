<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import CampaignCreationDrawer from "@/components/campaigns/CampaignCreationDrawer.vue";
import CampaignWorkbench from "@/components/campaigns/CampaignWorkbench.vue";
import CampaignList from "@/components/CampaignList.vue";
import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import JobList from "@/components/JobList.vue";
import ConsoleShell from "@/components/layout/ConsoleShell.vue";
import LlmConfigWorkspace from "@/components/llm/LlmConfigWorkspace.vue";
import MailWorkspace from "@/components/mail/MailWorkspace.vue";
import OperationsCenter from "@/components/jobs/OperationsCenter.vue";
import SitesWorkspace from "@/components/sites/SitesWorkspace.vue";
import EmailOutreachPanel from "@/components/mail/EmailOutreachPanel.vue";
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
  CreateLlmConfigRequest,
  CreateMailboxRequest,
  ConnectLinkedInSessionRequest,
  CreateCampaignRequest,
  CreateSiteRequest,
  EnrichedLead,
  HealthResponse,
  LeadRecipientSummary,
  LeadOutreachSummary,
  LinkedInSessionStatus,
  LlmConfigSummary,
  LlmProviderPreset,
  MailFolder,
  MailMessageDetail,
  MailMessageSummary,
  MailProviderConfig,
  MailboxSummary,
  ScrapedLead,
  ScrapeJobResultsResponse,
  ScrapeJobSummary,
  ScrapeSource,
  SendMailRequest,
  SiteDeployment,
  SiteSummary,
  UpdateLlmConfigRequest,
  UpdateMailboxRequest,
  UpdateSiteRequest,
} from "@/types";

const campaigns = ref<CampaignSummary[]>([]);
const selectedCampaignDetail = ref<CampaignDetail | null>(null);
const jobs = ref<ScrapeJobSummary[]>([]);
const selectedJobResults = ref<ScrapeJobResultsResponse | null>(null);
const health = ref<HealthResponse | null>(null);
const linkedinSession = ref<LinkedInSessionStatus | null>(null);
const mailProviders = ref<MailProviderConfig[]>([]);
const mailboxes = ref<MailboxSummary[]>([]);
const selectedMailboxId = ref<string | null>(null);
const currentMailFolder = ref<MailFolder>("inbox");
const mailMessages = ref<MailMessageSummary[]>([]);
const selectedMailMessage = ref<MailMessageDetail | null>(null);
const leadRecipients = ref<LeadRecipientSummary[]>([]);
const llmConfigs = ref<LlmConfigSummary[]>([]);
const llmProviders = ref<LlmProviderPreset[]>([]);
const selectedLlmConfigId = ref<string | null>(null);
const llmConfigWorkspaceRef = ref<InstanceType<typeof LlmConfigWorkspace> | null>(null);
const sites = ref<SiteSummary[]>([]);
const selectedSiteId = ref<string | null>(null);
const loadingSites = ref(false);
const busySite = ref(false);
const outreachLeads = ref<LeadOutreachSummary[]>([]);
const loadingOutreachLeads = ref(false);
const busyOutreach = ref(false);
const loadingLlmConfigs = ref(false);
const busyLlmConfig = ref(false);
const loadingCampaigns = ref(false);
const loadingCampaignDetail = ref(false);
const loadingJobs = ref(false);
const loadingJobResults = ref(false);
const loadingLinkedInSession = ref(false);
const loadingMailboxes = ref(false);
const loadingMailMessages = ref(false);
const loadingMailMessageDetail = ref(false);
const creatingCampaign = ref(false);
const syncingLinkedInSession = ref(false);
const savingMailbox = ref(false);
const sendingMail = ref(false);
const syncingMailboxId = ref<string | null>(null);
const campaignDrawerOpen = ref(false);
const mailComposerOpen = ref(false);
const mailTab = ref<"mailbox" | "outreach">("mailbox");
const message = ref<string | null>(null);
const messageTone = ref<"info" | "success" | "warning" | "danger">("info");
const campaignFilterQuery = ref("");
const campaignFilterStatus = ref<CampaignStatus | "all">("all");
const campaignFilterSource = ref<ScrapeSource | "all">("all");
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
const selectedMailbox = computed(
  () => mailboxes.value.find((mailbox) => mailbox.id === selectedMailboxId.value) ?? null,
);

const localeOptions = [
  { value: "zh-CN" as AppLocale, label: "简体中文" },
  { value: "en" as AppLocale, label: "EN" },
];

const navItems = computed(() => [
  { value: "overview" as ConsoleView, label: t("nav.overview"), hint: t("navHints.overview") },
  { value: "campaigns" as ConsoleView, label: t("nav.campaigns"), hint: t("navHints.campaigns") },
  { value: "mail" as ConsoleView, label: t("nav.mail"), hint: t("navHints.mail") },
  { value: "sites" as ConsoleView, label: t("nav.sites"), hint: t("navHints.sites") },
  { value: "llm" as ConsoleView, label: t("nav.llm"), hint: t("navHints.llm") },
  { value: "jobs" as ConsoleView, label: t("nav.jobs"), hint: t("navHints.jobs") },
  { value: "system" as ConsoleView, label: t("nav.system"), hint: t("navHints.system") },
]);

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
const filteredCampaigns = computed(() => {
  const needle = campaignFilterQuery.value.trim().toLowerCase();

  return campaigns.value.filter((campaign) => {
    const statusMatches =
      campaignFilterStatus.value === "all" || campaign.status === campaignFilterStatus.value;
    const sourceMatches =
      campaignFilterSource.value === "all" || campaign.source === campaignFilterSource.value;
    if (!statusMatches || !sourceMatches) {
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

const recentCampaigns = computed(() => campaigns.value.slice(0, 4));
const latestFailure = computed(
  () => campaigns.value.find((campaign) => campaign.status === "failed" || campaign.error_message) ?? null,
);
const sourceReadiness = computed(() => [
  { source: "google_maps" as ScrapeSource, state: t("common.enabled"), connected: true },
  {
    source: "linkedin" as ScrapeSource,
    state: linkedinSession.value?.connected ? t("common.connected") : t("common.disconnected"),
    connected: Boolean(linkedinSession.value?.connected),
  },
]);
const headerMeta = computed(() => {
  if (activeView.value === "campaigns") {
    return t("headerMeta.campaigns", { count: filteredCampaigns.value.length });
  }
  if (activeView.value === "jobs") {
    return t("headerMeta.jobs", { count: jobs.value.length });
  }
  if (activeView.value === "mail") {
    return t("headerMeta.mail", { count: mailboxes.value.length });
  }
  if (activeView.value === "llm") {
    return t("headerMeta.llm", { count: llmConfigs.value.length });
  }
  if (activeView.value === "sites") {
    return t("headerMeta.sites", { count: sites.value.length });
  }
  if (activeView.value === "system") {
    return t("headerMeta.system", {
      state: linkedinSession.value?.connected ? t("common.connected") : t("common.disconnected"),
    });
  }
  return t("headerMeta.overview", { running: runningCampaigns.value });
});

const activityLabel = computed(() => {
  const latest = campaigns.value[0];
  if (!latest) {
    return t("overview.metrics.latestActivityEmpty");
  }

  return `${t("overview.metrics.latestActivityPrefix")} ${new Intl.DateTimeFormat(
    currentLocale.value === "zh-CN" ? "zh-CN" : "en-GB",
    {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(new Date(latest.updated_at))}`;
});

const headerActionLabel = computed(() =>
  activeView.value === "mail" ? t("mail.compose") : t("actions.newCampaign"),
);

const hasActiveLlm = computed(() => llmConfigs.value.some((c) => c.is_active));

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

async function refreshMailProviders() {
  try {
    mailProviders.value = await api.listMailProviders();
  } catch (error) {
    setMessage(error);
  }
}

async function refreshMailboxes(options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingMailboxes.value = true;
  }

  try {
    mailboxes.value = await api.listMailboxes();
    if (!mailboxes.value.length) {
      selectedMailboxId.value = null;
      mailMessages.value = [];
      selectedMailMessage.value = null;
      return;
    }

    if (!selectedMailboxId.value || !mailboxes.value.some((mailbox) => mailbox.id === selectedMailboxId.value)) {
      selectedMailboxId.value = mailboxes.value[0].id;
    }
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingMailboxes.value = false;
    }
  }
}

async function refreshLeadRecipients() {
  try {
    leadRecipients.value = await api.listLeadRecipients();
  } catch (error) {
    setMessage(error);
  }
}

async function refreshMailMessages(options: { mode?: RefreshMode } = {}) {
  if (!selectedMailboxId.value) {
    mailMessages.value = [];
    selectedMailMessage.value = null;
    return;
  }

  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingMailMessages.value = true;
  }

  try {
    mailMessages.value = await api.listMailMessages(selectedMailboxId.value, currentMailFolder.value);
    if (!mailMessages.value.some((message) => message.id === selectedMailMessage.value?.id)) {
      selectedMailMessage.value = null;
    }
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingMailMessages.value = false;
    }
  }
}

async function loadMailMessage(messageId: string, options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingMailMessageDetail.value = true;
  }

  try {
    selectedMailMessage.value = await api.getMailMessage(messageId);
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingMailMessageDetail.value = false;
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
    messageTone.value = "success";
    campaignDrawerOpen.value = false;
    await Promise.all([refreshCampaigns(), refreshJobs()]);
    await selectCampaign(response.campaign.id);
  } catch (error) {
    setMessage(error);
  } finally {
    creatingCampaign.value = false;
  }
}

async function createMailbox(payload: CreateMailboxRequest) {
  savingMailbox.value = true;
  try {
    const mailbox = await api.createMailbox(payload);
    message.value = `${t("messages.mailboxConnectedPrefix")} ${mailbox.email_address}`;
    messageTone.value = "success";
    await Promise.all([refreshMailboxes(), refreshLeadRecipients()]);
    selectedMailboxId.value = mailbox.id;
    currentMailFolder.value = "inbox";
    await refreshMailMessages();
  } catch (error) {
    setMessage(error);
  } finally {
    savingMailbox.value = false;
  }
}

async function updateMailbox(mailboxId: string, payload: UpdateMailboxRequest) {
  savingMailbox.value = true;
  try {
    const mailbox = await api.updateMailbox(mailboxId, payload);
    message.value = `${t("messages.mailboxUpdatedPrefix")} ${mailbox.email_address}`;
    messageTone.value = "success";
    await refreshMailboxes();
  } catch (error) {
    setMessage(error);
  } finally {
    savingMailbox.value = false;
  }
}

async function syncMailbox(mailboxId: string) {
  syncingMailboxId.value = mailboxId;
  try {
    await api.syncMailbox(mailboxId);
    await Promise.all([refreshMailboxes(), refreshMailMessages(), refreshLeadRecipients()]);
    message.value = t("mail.mailboxSynced");
    messageTone.value = "success";
  } catch (error) {
    setMessage(error);
  } finally {
    syncingMailboxId.value = null;
  }
}

async function sendMail(payload: SendMailRequest) {
  sendingMail.value = true;
  try {
    const response = await api.sendMail(payload);
    message.value = `${t("messages.mailSentPrefix")} ${response.accepted.join(", ")}`;
    messageTone.value = "success";
    mailComposerOpen.value = false;
    currentMailFolder.value = "sent";
    await refreshMailMessages();
  } catch (error) {
    setMessage(error);
  } finally {
    sendingMail.value = false;
  }
}

async function connectLinkedInSession(payload: ConnectLinkedInSessionRequest) {
  syncingLinkedInSession.value = true;
  try {
    linkedinSession.value = await api.connectLinkedInSession(payload);
    message.value = t("messages.linkedinConnected");
    messageTone.value = "success";
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
    messageTone.value = "warning";
  } catch (error) {
    setMessage(error);
  } finally {
    syncingLinkedInSession.value = false;
  }
}

async function selectMailbox(mailboxId: string) {
  selectedMailboxId.value = mailboxId;
  currentMailFolder.value = "inbox";
  selectedMailMessage.value = null;
  mailComposerOpen.value = false;
  await refreshMailMessages();
}

async function selectMailFolder(folder: MailFolder) {
  currentMailFolder.value = folder;
  selectedMailMessage.value = null;
  await refreshMailMessages();
}

function setMessage(error: unknown) {
  message.value = error instanceof Error ? error.message : t("messages.unexpectedError");
  messageTone.value = "danger";
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

function openSystemView() {
  activeView.value = "system";
}

function openMailComposer() {
  activeView.value = "mail";
  mailComposerOpen.value = true;
}

function handlePrimaryAction() {
  if (activeView.value === "mail") {
    openMailComposer();
    return;
  }
  openCampaignView();
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
    messageTone.value = "warning";
    return;
  }

  downloadLeadsCsv(buildExportFilename("campaign", selectedCampaignDetail.value.name), leads);
}

function exportJobLeads(leads: ScrapedLead[]) {
  if (!selectedJobResults.value || !leads.length) {
    message.value = t("messages.exportUnavailable");
    messageTone.value = "warning";
    return;
  }

  downloadLeadsCsv(buildExportFilename("job", selectedJobResults.value.job.query), leads);
}

async function retryCampaign(campaignId: string) {
  retryingCampaignId.value = campaignId;
  try {
    const retried = await api.retryCampaign(campaignId);
    message.value = `${t("messages.campaignRetryQueued")} "${retried.name}"`;
    messageTone.value = "info";
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
    messageTone.value = "info";
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

async function handleEditLead(campaignId: string, leadId: string, updates: Record<string, string | null>) {
  try {
    const result = await api.updateCampaignLead(campaignId, leadId, updates);
    if (selectedCampaignDetail.value) {
      selectedCampaignDetail.value = {
        ...selectedCampaignDetail.value,
        total_leads: result.campaign.total_leads,
        average_score: result.campaign.average_score,
        priority_leads: result.campaign.priority_leads,
        results: selectedCampaignDetail.value.results.map((l) =>
          l.id === leadId ? result.lead : l,
        ),
      };
    }
    message.value = t("messages.leadUpdated");
    messageTone.value = "success";
  } catch (error) {
    setMessage(error);
  }
}

async function handleDeleteLead(campaignId: string, leadId: string) {
  try {
    await api.deleteCampaignLead(campaignId, leadId);
    await refreshSelectedCampaign();
    await refreshCampaignWorkspace({ mode: "silent" });
    message.value = t("messages.leadDeleted");
    messageTone.value = "success";
  } catch (error) {
    setMessage(error);
  }
}

async function refreshLlmProviders() {
  try {
    llmProviders.value = await api.getLlmProviders();
  } catch (error) {
    setMessage(error);
  }
}

async function refreshLlmConfigs(options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingLlmConfigs.value = true;
  }

  try {
    llmConfigs.value = await api.listLlmConfigs();
    if (!llmConfigs.value.length) {
      selectedLlmConfigId.value = null;
      return;
    }
    if (!selectedLlmConfigId.value || !llmConfigs.value.some((c) => c.id === selectedLlmConfigId.value)) {
      selectedLlmConfigId.value = llmConfigs.value[0].id;
    }
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingLlmConfigs.value = false;
    }
  }
}

async function createLlmConfig(payload: CreateLlmConfigRequest) {
  busyLlmConfig.value = true;
  try {
    const created = await api.createLlmConfig(payload);
    message.value = `${t("messages.llmConfigCreated")} "${created.display_name}"`;
    messageTone.value = "success";
    await refreshLlmConfigs();
    selectedLlmConfigId.value = created.id;
    llmConfigWorkspaceRef.value?.cancelForm();
  } catch (error) {
    setMessage(error);
  } finally {
    busyLlmConfig.value = false;
  }
}

async function updateLlmConfig(configId: string, payload: UpdateLlmConfigRequest) {
  busyLlmConfig.value = true;
  try {
    const updated = await api.updateLlmConfig(configId, payload);
    message.value = `${t("messages.llmConfigUpdated")} "${updated.display_name}"`;
    messageTone.value = "success";
    await refreshLlmConfigs();
    llmConfigWorkspaceRef.value?.cancelForm();
  } catch (error) {
    setMessage(error);
  } finally {
    busyLlmConfig.value = false;
  }
}

async function deleteLlmConfig(configId: string) {
  busyLlmConfig.value = true;
  try {
    await api.deleteLlmConfig(configId);
    message.value = t("messages.llmConfigDeleted");
    messageTone.value = "warning";
    await refreshLlmConfigs();
  } catch (error) {
    setMessage(error);
  } finally {
    busyLlmConfig.value = false;
  }
}

async function activateLlmConfig(configId: string) {
  busyLlmConfig.value = true;
  try {
    const activated = await api.activateLlmConfig(configId);
    message.value = `${t("messages.llmConfigActivated")} "${activated.display_name}"`;
    messageTone.value = "success";
    await refreshLlmConfigs();
  } catch (error) {
    setMessage(error);
  } finally {
    busyLlmConfig.value = false;
  }
}

async function deactivateLlmConfig(configId: string) {
  busyLlmConfig.value = true;
  try {
    const deactivated = await api.deactivateLlmConfig(configId);
    message.value = `${t("messages.llmConfigDeactivated")} "${deactivated.display_name}"`;
    messageTone.value = "info";
    await refreshLlmConfigs();
  } catch (error) {
    setMessage(error);
  } finally {
    busyLlmConfig.value = false;
  }
}

async function selectLlmConfig(configId: string) {
  selectedLlmConfigId.value = configId;
}

async function refreshSites(options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingSites.value = true;
  }

  try {
    sites.value = await api.listSites();
    if (!sites.value.length) {
      selectedSiteId.value = null;
      return;
    }
    if (!selectedSiteId.value || !sites.value.some((s) => s.id === selectedSiteId.value)) {
      selectedSiteId.value = sites.value[0].id;
    }
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingSites.value = false;
    }
  }
}

async function createSite(payload: CreateSiteRequest) {
  busySite.value = true;
  try {
    const created = await api.createSite(payload);
    message.value = `${t("messages.siteCreated")} "${created.display_name}"`;
    messageTone.value = "success";
    await refreshSites();
    selectedSiteId.value = created.id;
  } catch (error) {
    setMessage(error);
  } finally {
    busySite.value = false;
  }
}

async function updateSite(siteId: string, payload: UpdateSiteRequest) {
  busySite.value = true;
  try {
    const updated = await api.updateSite(siteId, payload);
    message.value = `${t("messages.siteUpdated")} "${updated.display_name}"`;
    messageTone.value = "success";
    await refreshSites();
  } catch (error) {
    setMessage(error);
  } finally {
    busySite.value = false;
  }
}

async function deleteSite(siteId: string) {
  busySite.value = true;
  try {
    await api.deleteSite(siteId);
    message.value = t("messages.siteDeleted");
    messageTone.value = "warning";
    await refreshSites();
  } catch (error) {
    setMessage(error);
  } finally {
    busySite.value = false;
  }
}

async function deploySite(siteId: string) {
  busySite.value = true;
  try {
    await api.deploySite(siteId);
    message.value = t("messages.siteDeployStarted");
    messageTone.value = "info";
    await refreshSites();
  } catch (error) {
    setMessage(error);
  } finally {
    busySite.value = false;
  }
}

async function selectSite(siteId: string) {
  selectedSiteId.value = siteId;
}

async function refreshOutreachLeads(options: { mode?: RefreshMode } = {}) {
  const mode = options.mode ?? "visible";
  if (mode === "visible") {
    loadingOutreachLeads.value = true;
  }
  try {
    outreachLeads.value = await api.listOutreachLeads();
  } catch (error) {
    setMessage(error);
  } finally {
    if (mode === "visible") {
      loadingOutreachLeads.value = false;
    }
  }
}

function handleOutreachMessage(text: string, tone: "info" | "success" | "warning" | "danger") {
  message.value = text;
  messageTone.value = tone;
}

async function bootstrap() {
  await Promise.all([
    refreshHealth(),
    refreshCampaigns(),
    refreshJobs(),
    refreshLinkedInSession(),
    refreshMailProviders(),
    refreshMailboxes(),
    refreshLeadRecipients(),
    refreshLlmProviders(),
    refreshLlmConfigs(),
    refreshSites(),
    refreshOutreachLeads(),
  ]);
  if (selectedCampaignId.value) {
    await refreshSelectedCampaign();
  }
}

watch(
  () => activeView.value,
  async (view) => {
    if (view === "mail" && selectedMailboxId.value) {
      await refreshMailMessages({ mode: "silent" });
    }
  },
);

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
        refreshLlmConfigs({ mode: "silent" }),
        refreshSites({ mode: "silent" }),
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
      :meta="headerMeta"
      :active-locale="currentLocale"
      :locale-options="localeOptions"
      :action-label="headerActionLabel"
      @select-view="setActiveView"
      @change-locale="setLocale"
      @action="handlePrimaryAction"
    >
      <CampaignCreationDrawer
        :open="campaignDrawerOpen"
        :busy="creatingCampaign"
        :linkedin-connected="Boolean(linkedinSession?.connected)"
        @close="campaignDrawerOpen = false"
        @submit="createCampaign"
      />

      <InlineStatusNotice
        v-if="message"
        class="global-message"
        :title="message"
        :tone="messageTone"
      />

      <section v-if="activeView === 'overview'" class="view-grid overview-shell">
        <section class="panel spotlight-panel">
          <div class="spotlight-copy">
            <p class="panel-kicker">{{ t("overview.spotlight.kicker") }}</p>
            <h2>{{ t("overview.spotlight.title") }}</h2>
            <p class="drawer-copy">{{ t("overview.spotlight.description") }}</p>
            <div class="panel-actions spotlight-actions">
              <button class="action-button" type="button" @click="openCampaignView">
                {{ t("actions.newCampaign") }}
              </button>
              <button class="ghost-button" type="button" @click="openSystemView">
                {{ t("actions.openSystem") }}
              </button>
            </div>
          </div>

          <div class="spotlight-side">
            <div class="hero-status">
              <div v-for="card in statusCards" :key="card.label" class="hero-status-card">
                <span class="summary-label">{{ card.label }}</span>
                <strong>{{ card.value }}</strong>
              </div>
            </div>
            <div class="source-readiness-list">
              <article
                v-for="item in sourceReadiness"
                :key="item.source"
                class="source-readiness-card"
                :data-connected="item.connected"
              >
                <span class="summary-label">{{ t(`sources.${item.source}`) }}</span>
                <strong>{{ item.state }}</strong>
              </article>
            </div>
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

        <section class="overview-rail">
          <section class="panel rail-panel">
            <div class="panel-heading">
              <p class="panel-kicker">{{ t("overview.spotlight.recentTitle") }}</p>
              <h2>{{ t("campaigns.queueTitle") }}</h2>
            </div>
            <div v-if="recentCampaigns.length" class="compact-stack">
              <button
                v-for="campaign in recentCampaigns"
                :key="campaign.id"
                class="compact-item"
                type="button"
                @click="selectCampaign(campaign.id)"
              >
                <div class="compact-item-top">
                  <strong>{{ campaign.name }}</strong>
                  <StatusBadge :status="campaign.status" />
                </div>
                <p class="job-meta">{{ t(`sources.${campaign.source}`) }} / {{ campaign.location }}</p>
              </button>
            </div>
            <div v-else class="empty-state compact-empty">
              <p>{{ t("overview.spotlight.emptyRecent") }}</p>
            </div>
          </section>

          <section class="panel rail-panel">
            <div class="panel-heading">
              <p class="panel-kicker">{{ t("overview.spotlight.healthTitle") }}</p>
              <h2>{{ t("runtime.serviceHealth") }}</h2>
            </div>
            <dl class="health-grid compact-health-grid">
              <div>
                <dt>{{ t("runtime.timeout") }}</dt>
                <dd>{{ health?.scraper.timeout_ms ?? 0 }} ms</dd>
              </div>
              <div>
                <dt>{{ t("runtime.tlsVerify") }}</dt>
                <dd>{{ health?.scraper.verify_tls ? t("common.enabled") : t("common.disabled") }}</dd>
              </div>
              <div>
                <dt>{{ t("runtime.quietRefresh") }}</dt>
                <dd>{{ t("runtime.quietRefreshValue") }}</dd>
              </div>
            </dl>

            <InlineStatusNotice
              v-if="latestFailure"
              :title="t('notices.failureTitle')"
              :detail="latestFailure.error_message ?? latestFailure.name"
              tone="warning"
            />
          </section>
        </section>
      </section>

      <section v-else-if="activeView === 'campaigns'" class="view-grid campaign-layout">
        <InlineStatusNotice
          v-if="!linkedinSession?.connected"
          :title="t('notices.offlineTitle')"
          :detail="t('notices.offlineDetail')"
          tone="info"
        />

        <CampaignList
          :campaigns="filteredCampaigns"
          :selected-campaign-id="selectedCampaignId"
          :loading="loadingCampaigns"
          :filter-query="campaignFilterQuery"
          :filter-status="campaignFilterStatus"
          :filter-source="campaignFilterSource"
          :total-campaigns="campaigns.length"
          @select="selectCampaign"
          @refresh="refreshCampaignWorkspace()"
          @update-filter-query="campaignFilterQuery = $event"
          @update-filter-status="campaignFilterStatus = $event"
          @update-filter-source="campaignFilterSource = $event"
        />

        <CampaignWorkbench
          :campaign="selectedCampaignDetail"
          :linked-job="linkedJob"
          :loading="loadingCampaignDetail"
          :retrying="retryingCampaignId === selectedCampaignDetail?.id"
          @retry="retryCampaign"
          @export="exportCampaignLeads"
          @edit-lead="handleEditLead"
          @delete-lead="handleDeleteLead"
        />
      </section>

      <section v-else-if="activeView === 'mail'" class="view-grid">
        <div class="mail-folder-tabs" style="margin-bottom:0.5rem">
          <button class="mail-folder-tab" :class="{ active: mailTab === 'mailbox' }" type="button"
            @click="mailTab = 'mailbox'">{{ t("mail.inbox") }}</button>
          <button class="mail-folder-tab" :class="{ active: mailTab === 'outreach' }" type="button"
            @click="mailTab = 'outreach'">{{ t("outreach.tabLabel") }}</button>
        </div>
        <template v-if="mailTab === 'mailbox'">
        <MailWorkspace
          :mailboxes="mailboxes"
          :providers="mailProviders"
          :selected-mailbox-id="selectedMailboxId"
          :folder="currentMailFolder"
          :messages="mailMessages"
          :selected-message="selectedMailMessage"
          :lead-recipients="leadRecipients"
          :composer-open="mailComposerOpen"
          :loading-mailboxes="loadingMailboxes"
          :loading-messages="loadingMailMessages"
          :loading-message-detail="loadingMailMessageDetail"
          :saving-mailbox="savingMailbox"
          :sending-mail="sendingMail"
          :syncing-mailbox-id="syncingMailboxId"
          @select-mailbox="selectMailbox"
          @select-folder="selectMailFolder"
          @select-message="loadMailMessage"
          @create-mailbox="createMailbox"
          @update-mailbox="updateMailbox"
          @sync-mailbox="syncMailbox"
          @send-mail="sendMail"
          @update-composer-open="mailComposerOpen = $event"
        />
        </template>
        <EmailOutreachPanel
          v-else
          :leads="outreachLeads"
          :mailboxes="mailboxes"
          :loading-leads="loadingOutreachLeads"
          :busy="busyOutreach"
          :has-active-llm="hasActiveLlm"
          @refresh-leads="refreshOutreachLeads"
          @message="handleOutreachMessage"
        />
      </section>

      <section v-else-if="activeView === 'llm'" class="view-grid">
        <LlmConfigWorkspace
          ref="llmConfigWorkspaceRef"
          :configs="llmConfigs"
          :providers="llmProviders"
          :selected-config-id="selectedLlmConfigId"
          :loading-configs="loadingLlmConfigs"
          :busy="busyLlmConfig"
          @select-config="selectLlmConfig"
          @create-config="createLlmConfig"
          @update-config="updateLlmConfig"
          @delete-config="deleteLlmConfig"
          @activate-config="activateLlmConfig"
          @deactivate-config="deactivateLlmConfig"
        />
      </section>

      <section v-else-if="activeView === 'sites'" class="view-grid">
        <SitesWorkspace
          :sites="sites"
          :selected-site-id="selectedSiteId"
          :loading-sites="loadingSites"
          :busy="busySite"
          @select-site="selectSite"
          @create-site="createSite"
          @update-site="updateSite"
          @delete-site="deleteSite"
          @deploy-site="deploySite"
        />
      </section>

      <section v-else-if="activeView === 'jobs'" class="view-grid jobs-layout">
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

      <section v-else class="view-grid system-layout">
        <InlineStatusNotice
          v-if="linkedinSession?.last_error"
          :title="t('notices.failureTitle')"
          :detail="linkedinSession.last_error"
          tone="warning"
        />

        <section class="system-grid">
          <section class="panel panel-health">
            <div class="panel-heading">
              <p class="panel-kicker">{{ t("runtime.runtimeKicker") }}</p>
              <h2>{{ t("runtime.systemDetails") }}</h2>
            </div>

            <dl class="health-grid">
              <div>
                <dt>{{ t("runtime.timeout") }}</dt>
                <dd>{{ health?.scraper.timeout_ms ?? 0 }} ms</dd>
              </div>
              <div>
                <dt>{{ t("runtime.tlsVerify") }}</dt>
                <dd>{{ health?.scraper.verify_tls ? t("common.enabled") : t("common.disabled") }}</dd>
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
      </section>
    </ConsoleShell>
  </div>
</template>
