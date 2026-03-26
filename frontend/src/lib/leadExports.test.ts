import { describe, expect, it } from "vitest";

import { createLeadsCsv } from "@/lib/leadExports";
import type { EnrichedLead } from "@/types";

describe("createLeadsCsv", () => {
  it("includes email and intelligence columns in exported csv", () => {
    const csv = createLeadsCsv([
      {
        name: "Atlas Coffee",
        address: "Seattle",
        phone: "02065550199",
        email: "hello@atlas.example",
        website: "https://atlas.example",
        reference_link: "https://maps.google.com/example",
        rating: "4.9",
        has_website: true,
        source: "google_maps",
        scraped_at: "2026-03-26T00:00:00Z",
        intelligence: {
          score: 91,
          category: "A",
          priority: "HIGH",
          recommendation: "Call first",
          factors: {
            data_completeness: 90,
            business_quality: 90,
            digital_presence: 90,
            location_value: 90,
            industry_potential: 90,
            contactability: 90,
          },
        },
      } satisfies EnrichedLead,
    ]);

    expect(csv).toContain("email");
    expect(csv).toContain("hello@atlas.example");
    expect(csv).toContain("HIGH");
    expect(csv).toContain("91");
  });
});
