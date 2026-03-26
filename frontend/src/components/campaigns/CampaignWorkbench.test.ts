import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CampaignWorkbench from "@/components/campaigns/CampaignWorkbench.vue";
import type { CampaignDetail, ScrapeJobSummary } from "@/types";

const campaign: CampaignDetail = {
  id: "campaign-1",
  job_id: "job-1",
  name: "Jakarta coffee",
  industry: "restaurant",
  location: "Jakarta",
  query: "Coffee shops Jakarta",
  source: "google_maps",
  max_results: 20,
  status: "completed",
  total_leads: 5,
  average_score: 84,
  priority_leads: 2,
  error_message: null,
  created_at: "2026-03-26T00:00:00Z",
  started_at: "2026-03-26T00:01:00Z",
  completed_at: "2026-03-26T00:02:00Z",
  updated_at: "2026-03-26T00:02:00Z",
  results: [],
};

const linkedJob: ScrapeJobSummary = {
  id: "job-1",
  campaign_id: "campaign-1",
  query: "Coffee shops Jakarta",
  source: "google_maps",
  max_results: 20,
  status: "completed",
  result_count: 5,
  error_message: null,
  created_at: "2026-03-26T00:00:00Z",
  started_at: "2026-03-26T00:01:00Z",
  completed_at: "2026-03-26T00:02:00Z",
  updated_at: "2026-03-26T00:02:00Z",
};

describe("CampaignWorkbench", () => {
  it("shows selected campaign summary before telemetry", () => {
    const wrapper = mount(CampaignWorkbench, {
      props: {
        campaign,
        linkedJob,
        loading: false,
        retrying: false,
      },
    });

    expect(wrapper.text()).toContain("Selected campaign");
    expect(wrapper.text()).toContain("Lead review");
    expect(wrapper.text()).toContain("Execution telemetry");
  });
});
