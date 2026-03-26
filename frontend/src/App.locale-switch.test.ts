import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({
  api: {
    getHealth: vi.fn(async () => ({
      status: "ok",
      database: {
        path: "backend/data/app.db",
        healthy: true,
      },
      scraper: {
        engine: "scrapling",
        timeout_ms: 15000,
        verify_tls: false,
      },
    })),
    listCampaigns: vi.fn(async () => []),
    listJobs: vi.fn(async () => []),
    getCampaign: vi.fn(),
    getJobResults: vi.fn(),
    getLinkedInSession: vi.fn(async () => ({
      source: "linkedin",
      connected: false,
      account_label: null,
      last_error: null,
      updated_at: null,
    })),
    connectLinkedInSession: vi.fn(),
    disconnectLinkedInSession: vi.fn(),
    retryCampaign: vi.fn(),
    retryJob: vi.fn(),
    createCampaign: vi.fn(),
  },
}));

import App from "@/App.vue";

describe("App locale switch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("updates navigation and action labels when locale changes", async () => {
    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.text()).toContain("Overview");
    expect(wrapper.text()).toContain("New Campaign");

    await wrapper.findAll("button.locale-button")[0].trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("总览");
    expect(wrapper.text()).toContain("新建活动");

    wrapper.unmount();
  });
});
