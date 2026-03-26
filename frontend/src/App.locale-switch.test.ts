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
    listMailProviders: vi.fn(async () => []),
    listMailboxes: vi.fn(async () => []),
    createMailbox: vi.fn(),
    updateMailbox: vi.fn(),
    syncMailbox: vi.fn(),
    listMailMessages: vi.fn(async () => []),
    getMailMessage: vi.fn(),
    sendMail: vi.fn(),
    listLeadRecipients: vi.fn(async () => []),
  },
}));

import App from "@/App.vue";

describe("App locale switch", () => {
  afterEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("updates navigation and action labels when locale changes", async () => {
    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.text()).toContain("Overview");
    expect(wrapper.text()).toContain("New Campaign");

    await wrapper.findAll("button.locale-button")[0].trigger("click");
    await flushPromises();

    expect(wrapper.text()).not.toContain("Overview");
    expect(wrapper.text()).not.toContain("New Campaign");

    wrapper.unmount();
  });
});
