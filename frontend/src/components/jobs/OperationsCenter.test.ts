import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import OperationsCenter from "@/components/jobs/OperationsCenter.vue";

describe("OperationsCenter", () => {
  it("keeps raw jobs behind an explicit operations heading", () => {
    const wrapper = mount(OperationsCenter);

    expect(wrapper.text()).toContain("Operations center");
    expect(wrapper.text()).toContain("Raw jobs and results");
  });
});
