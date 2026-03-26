import type { EnrichedLead, ScrapedLead } from "@/types";

type ExportableLead = ScrapedLead | EnrichedLead;

const CSV_HEADERS = [
  "name",
  "address",
  "location",
  "phone",
  "email",
  "website",
  "headline",
  "current_company",
  "profile_url",
  "rating",
  "priority",
  "score",
  "category",
  "reference_link",
  "source",
  "scraped_at",
] as const;

function escapeCsvValue(value: string | number | null | undefined): string {
  const text = value == null ? "" : String(value);
  if (text.includes(",") || text.includes("\"") || text.includes("\n")) {
    return `"${text.replaceAll("\"", "\"\"")}"`;
  }
  return text;
}

export function createLeadsCsv(leads: ExportableLead[]): string {
  const rows = leads.map((lead) => [
    lead.name,
    lead.address,
    lead.location,
    lead.phone,
    lead.email,
    lead.website,
    lead.headline,
    lead.current_company,
    lead.profile_url,
    lead.rating,
    "intelligence" in lead ? lead.intelligence.priority : null,
    "intelligence" in lead ? lead.intelligence.score : null,
    "intelligence" in lead ? lead.intelligence.category : null,
    lead.reference_link,
    lead.source,
    lead.scraped_at,
  ]);

  return [
    CSV_HEADERS.join(","),
    ...rows.map((row) => row.map((value) => escapeCsvValue(value)).join(",")),
  ].join("\n");
}

export function downloadLeadsCsv(filename: string, leads: ExportableLead[]): void {
  const csv = createLeadsCsv(leads);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}
