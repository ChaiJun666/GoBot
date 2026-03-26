import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  CampaignDetail,
  CampaignSummary,
  HealthResponse,
  ScrapeJobResultsResponse,
  ScrapeJobSummary,
} from "@/types";

const apiMocks = vi.hoisted(() => ({
  getHealth: vi.fn(),
  listCampaigns: vi.fn(),
  listJobs: vi.fn(),
  getCampaign: vi.fn(),
  getJobResults: vi.fn(),
  getLinkedInSession: vi.fn(),
  connectLinkedInSession: vi.fn(),
  disconnectLinkedInSession: vi.fn(),
  retryCampaign: vi.fn(),
  retryJob: vi.fn(),
  createCampaign: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  api: apiMocks,
}));

import App from "@/App.vue";

const healthResponse: HealthResponse = {
  status: "ok",
  database: {
    path: "backend/data/app.db",
    healthy: true,
  },
  scraper: {
    engine: "scrapling",
    timeout_ms: 15000,
    verify_tls: true,
  },
};

const campaigns: CampaignSummary[] = [
  {
    id: "campaign-1",
    job_id: "job-1",
    name: "Seattle cafes",
    industry: "hospitality",
    location: "Seattle",
    query: "Seattle cafes",
    query_config: { query: "Seattle cafes" },
    source: "google_maps",
    max_results: 20,
    status: "running",
    total_leads: 12,
    average_score: 71,
    priority_leads: 3,
    error_message: null,
    created_at: "2026-03-26T00:00:00Z",
    started_at: "2026-03-26T00:01:00Z",
    completed_at: null,
    updated_at: "2026-03-26T00:02:00Z",
  },
  {
    id: "campaign-2",
    job_id: "job-2",
    name: "Portland gyms",
    industry: "fitness",
    location: "Portland",
    query: "Portland gyms",
    query_config: { query: "Portland gyms" },
    source: "google_maps",
    max_results: 15,
    status: "completed",
    total_leads: 8,
    average_score: 82,
    priority_leads: 4,
    error_message: null,
    created_at: "2026-03-26T01:00:00Z",
    started_at: "2026-03-26T01:01:00Z",
    completed_at: "2026-03-26T01:02:00Z",
    updated_at: "2026-03-26T01:02:00Z",
  },
];

const jobs: ScrapeJobSummary[] = [
  {
    id: "job-1",
    campaign_id: "campaign-1",
    query: "Seattle cafes",
    query_config: { query: "Seattle cafes" },
    source: "google_maps",
    max_results: 20,
    status: "running",
    result_count: 12,
    error_message: null,
    created_at: "2026-03-26T00:00:00Z",
    started_at: "2026-03-26T00:01:00Z",
    completed_at: null,
    updated_at: "2026-03-26T00:02:00Z",
  },
  {
    id: "job-2",
    campaign_id: "campaign-2",
    query: "Portland gyms",
    query_config: { query: "Portland gyms" },
    source: "google_maps",
    max_results: 15,
    status: "completed",
    result_count: 8,
    error_message: null,
    created_at: "2026-03-26T01:00:00Z",
    started_at: "2026-03-26T01:01:00Z",
    completed_at: "2026-03-26T01:02:00Z",
    updated_at: "2026-03-26T01:02:00Z",
  },
];

const campaignDetails = new Map<string, CampaignDetail>(
  campaigns.map((campaign) => [
    campaign.id,
    {
      ...campaign,
      results: [],
    },
  ]),
);

const jobResults = new Map<string, ScrapeJobResultsResponse>(
  jobs.map((job) => [
    job.id,
    {
      job,
      results: [],
    },
  ]),
);

describe("App polling behavior", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    window.localStorage.clear();

    apiMocks.getHealth.mockResolvedValue(healthResponse);
    apiMocks.listCampaigns.mockResolvedValue(campaigns);
    apiMocks.listJobs.mockResolvedValue(jobs);
    apiMocks.getLinkedInSession.mockResolvedValue({
      source: "linkedin",
      connected: false,
      account_label: null,
      last_error: null,
      updated_at: null,
    });
    apiMocks.getCampaign.mockImplementation(async (campaignId: string) => {
      const campaign = campaignDetails.get(campaignId);
      if (!campaign) {
        throw new Error(`missing campaign ${campaignId}`);
      }
      return campaign;
    });
    apiMocks.getJobResults.mockImplementation(async (jobId: string) => {
      const payload = jobResults.get(jobId);
      if (!payload) {
        throw new Error(`missing job ${jobId}`);
      }
      return payload;
    });
    apiMocks.createCampaign.mockReset();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("keeps polling silent and preserves the active view", async () => {
    const wrapper = mount(App);
    await flushPromises();

    const navButtons = wrapper.findAll(".primary-nav-button");
    await navButtons[3].trigger("click");
    await flushPromises();

    expect(wrapper.get(".primary-nav-button.active").text()).toBe("System");

    await navButtons[1].trigger("click");
    await flushPromises();

    expect(wrapper.get(".primary-nav-button.active").text()).toBe("Campaigns");
    expect(wrapper.text()).not.toContain("Refresh...");

    await vi.advanceTimersByTimeAsync(5000);
    await flushPromises();

    expect(wrapper.get(".primary-nav-button.active").text()).toBe("Campaigns");
    expect(wrapper.text()).not.toContain("Refresh...");

    wrapper.unmount();
  });

  it("keeps campaign selection inside the campaigns workspace", async () => {
    const wrapper = mount(App);
    await flushPromises();

    await wrapper.findAll(".primary-nav-button")[1].trigger("click");
    await flushPromises();

    const cards = wrapper.findAll(".job-card");
    await cards[1].trigger("click");
    await flushPromises();

    expect(wrapper.get(".primary-nav-button.active").text()).toBe("Campaigns");
    expect(wrapper.find(".campaign-workbench").exists()).toBe(true);
    expect(wrapper.find(".operations-center").exists()).toBe(false);
    expect(apiMocks.getCampaign).toHaveBeenLastCalledWith("campaign-2");

    wrapper.unmount();
  });
});
