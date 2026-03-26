import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import LinkedInSessionCard from "@/components/system/LinkedInSessionCard.vue";
import type { LinkedInSessionStatus } from "@/types";

const disconnectedSession: LinkedInSessionStatus = {
  source: "linkedin",
  connected: false,
  account_label: null,
  last_error: null,
  updated_at: null,
};

const connectedSession: LinkedInSessionStatus = {
  source: "linkedin",
  connected: true,
  account_label: "operator@example.com",
  last_error: null,
  updated_at: "2026-03-26T12:00:00Z",
};

describe("LinkedInSessionCard", () => {
  it("shows credential inputs only when the session is disconnected", () => {
    const disconnectedWrapper = mount(LinkedInSessionCard, {
      props: {
        session: disconnectedSession,
        busy: false,
      },
    });

    expect(disconnectedWrapper.find('input[autocomplete="username"]').exists()).toBe(true);
    expect(disconnectedWrapper.find('input[autocomplete="current-password"]').exists()).toBe(true);
    expect(disconnectedWrapper.text()).toContain("Connect session");

    const connectedWrapper = mount(LinkedInSessionCard, {
      props: {
        session: connectedSession,
        busy: false,
      },
    });

    expect(connectedWrapper.find('input[autocomplete="username"]').exists()).toBe(false);
    expect(connectedWrapper.find('input[autocomplete="current-password"]').exists()).toBe(false);
    expect(connectedWrapper.text()).toContain("Disconnect");
  });

  it("toggles password visibility with the eye button", async () => {
    const wrapper = mount(LinkedInSessionCard, {
      props: {
        session: disconnectedSession,
        busy: false,
      },
    });

    const passwordInput = wrapper.get('input[autocomplete="current-password"]');
    const toggle = wrapper.get('button[aria-label="Show password"]');

    expect(passwordInput.attributes("type")).toBe("password");

    await toggle.trigger("click");
    expect(wrapper.get('input[autocomplete="current-password"]').attributes("type")).toBe("text");
    expect(wrapper.get('button[aria-label="Hide password"]').exists()).toBe(true);

    await wrapper.get('button[aria-label="Hide password"]').trigger("click");
    expect(wrapper.get('input[autocomplete="current-password"]').attributes("type")).toBe("password");
  });

  it("does not submit the form when toggling password visibility", async () => {
    const wrapper = mount(LinkedInSessionCard, {
      props: {
        session: disconnectedSession,
        busy: false,
      },
    });

    await wrapper.get('input[autocomplete="username"]').setValue("user@example.com");
    await wrapper.get('input[autocomplete="current-password"]').setValue("secret");
    await wrapper.get('button[aria-label="Show password"]').trigger("click");

    expect(wrapper.emitted("connect")).toBeUndefined();
  });
});
