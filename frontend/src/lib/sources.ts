import type {
  CampaignSummary,
  LinkedInQueryConfig,
  ScrapeJobSummary,
  ScrapeSource,
  SourceQueryConfig,
} from "@/types";

export function getSourceLabel(source: ScrapeSource): string {
  return source === "linkedin" ? "LinkedIn" : "Google Maps";
}

export function buildLinkedInQuerySummary(config: LinkedInQueryConfig): string {
  return [config.keywords, config.title, config.company, config.location]
    .filter(Boolean)
    .join(" | ");
}

export function getQueryConfigLabel(value: CampaignSummary | ScrapeJobSummary): string {
  return value.query || describeSourceQuery(value.query_config, value.source);
}

export function describeSourceQuery(config: SourceQueryConfig | null, source: ScrapeSource): string {
  if (!config) {
    return "";
  }
  if (source === "linkedin") {
    return buildLinkedInQuerySummary(config as LinkedInQueryConfig);
  }
  return "query" in config ? config.query : "";
}
