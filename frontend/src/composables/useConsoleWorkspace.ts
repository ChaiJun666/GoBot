import { computed, ref } from "vue";

import type { CampaignSummary, ScrapeJobSummary } from "@/types";

export type ConsoleView = "overview" | "campaigns" | "mail" | "jobs" | "system" | "llm";

type WorkspaceCampaign = Pick<CampaignSummary, "id" | "job_id" | "status" | "total_leads">;
type WorkspaceJob = Pick<ScrapeJobSummary, "id" | "campaign_id" | "status" | "result_count">;

interface WorkspaceSeed {
  campaigns?: WorkspaceCampaign[];
  jobs?: WorkspaceJob[];
  initialView?: ConsoleView;
}

export function createConsoleWorkspace(seed: WorkspaceSeed = {}) {
  const campaigns = ref(seed.campaigns ?? []);
  const jobs = ref(seed.jobs ?? []);
  const activeView = ref<ConsoleView>(seed.initialView ?? "overview");
  const selectedCampaignId = ref<string | null>(campaigns.value[0]?.id ?? null);
  const selectedJobId = ref<string | null>(null);

  const selectedCampaign = computed(
    () => campaigns.value.find((campaign) => campaign.id === selectedCampaignId.value) ?? null,
  );

  const linkedJob = computed(
    () => jobs.value.find((job) => job.id === selectedCampaign.value?.job_id) ?? null,
  );

  function setCampaigns(next: WorkspaceCampaign[]) {
    campaigns.value = next;
    if (!next.some((campaign) => campaign.id === selectedCampaignId.value)) {
      selectedCampaignId.value = next[0]?.id ?? null;
    }
  }

  function setJobs(next: WorkspaceJob[]) {
    jobs.value = next;
    if (!next.some((job) => job.id === selectedJobId.value)) {
      selectedJobId.value = linkedJob.value?.id ?? null;
    }
  }

  function selectCampaign(campaignId: string) {
    selectedCampaignId.value = campaignId;
    selectedJobId.value =
      campaigns.value.find((campaign) => campaign.id === campaignId)?.job_id ?? null;
    activeView.value = "campaigns";
  }

  function selectJob(jobId: string) {
    selectedJobId.value = jobId;
    activeView.value = "jobs";
  }

  return {
    activeView,
    campaigns,
    jobs,
    linkedJob,
    selectedCampaign,
    selectedCampaignId,
    selectedJobId,
    selectCampaign,
    selectJob,
    setCampaigns,
    setJobs,
  };
}
