import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CampaignCreationDrawer from "@/components/campaigns/CampaignCreationDrawer.vue";

function mountDrawer(linkedinConnected = true) {
  return mount(CampaignCreationDrawer, {
    props: {
      open: true,
      busy: false,
      linkedinConnected,
    },
  });
}

describe("CampaignCreationDrawer", () => {
  it("disables launch until required Google Maps fields are filled", async () => {
    const wrapper = mountDrawer();
    const launchButton = wrapper.get('button[type="submit"]');

    expect((launchButton.element as HTMLButtonElement).disabled).toBe(true);

    await wrapper.get('input[placeholder="Jakarta coffee market"]').setValue("Jakarta coffee");
    await wrapper.get('input[placeholder="Jakarta"]').setValue("Jakarta");
    await wrapper.get('textarea[placeholder="Coffee shops Jakarta Selatan"]').setValue(
      "Coffee shops Jakarta",
    );

    expect((wrapper.get('button[type="submit"]').element as HTMLButtonElement).disabled).toBe(
      false,
    );
  });

  it("keeps LinkedIn launch disabled until the shared session is connected", async () => {
    const wrapper = mountDrawer(false);

    await wrapper.get('input[placeholder="Jakarta coffee market"]').setValue("Growth leads");
    await wrapper.get('input[placeholder="Jakarta"]').setValue("Singapore");
    await wrapper.get("select").setValue("linkedin");
    await wrapper.get('input[placeholder="growth marketer"]').setValue("founder");

    expect((wrapper.get('button[type="submit"]').element as HTMLButtonElement).disabled).toBe(
      true,
    );
  });
});
