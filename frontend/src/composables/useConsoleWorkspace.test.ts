import { describe, expect, it } from "vitest";

import { createConsoleWorkspace } from "@/composables/useConsoleWorkspace";

describe("createConsoleWorkspace", () => {
  it("keeps campaign workflow primary and links the selected job", () => {
    const workspace = createConsoleWorkspace({
      campaigns: [{ id: "campaign-1", job_id: "job-1", status: "completed", total_leads: 3 }],
      jobs: [{ id: "job-1", campaign_id: "campaign-1", status: "completed", result_count: 3 }],
    });

    workspace.selectCampaign("campaign-1");

    expect(workspace.activeView.value).toBe("campaigns");
    expect(workspace.linkedJob.value?.id).toBe("job-1");
    expect(workspace.selectedJobId.value).toBe("job-1");
  });

  it("falls back to the first available campaign when the selection disappears", () => {
    const workspace = createConsoleWorkspace({
      campaigns: [
        { id: "campaign-1", job_id: "job-1", status: "completed", total_leads: 3 },
        { id: "campaign-2", job_id: "job-2", status: "queued", total_leads: 0 },
      ],
    });

    workspace.selectCampaign("campaign-2");
    workspace.setCampaigns([{ id: "campaign-1", job_id: "job-1", status: "completed", total_leads: 3 }]);

    expect(workspace.selectedCampaignId.value).toBe("campaign-1");
  });
});
