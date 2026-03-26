import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ConsoleShell from "@/components/layout/ConsoleShell.vue";

describe("ConsoleShell", () => {
  it("renders overview, campaigns, jobs, and system navigation", () => {
    const wrapper = mount(ConsoleShell, {
      props: {
        activeView: "overview",
        navItems: [
          { value: "overview", label: "Overview" },
          { value: "campaigns", label: "Campaigns" },
          { value: "mail", label: "Mail" },
          { value: "jobs", label: "Jobs" },
          { value: "system", label: "System" },
        ],
        title: "Run campaigns",
        subtitle: "Inspect campaigns and jobs.",
        activeLocale: "en",
        localeOptions: [
          { value: "zh-CN", label: "简体中文" },
          { value: "en", label: "EN" },
        ],
        actionLabel: "New Campaign",
      },
    });

    expect(wrapper.find('[aria-label="Primary"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Overview");
    expect(wrapper.text()).toContain("Campaigns");
    expect(wrapper.text()).toContain("Mail");
    expect(wrapper.text()).toContain("Jobs");
    expect(wrapper.text()).toContain("System");
  });
});
