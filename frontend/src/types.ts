export type ScrapeJobStatus = "queued" | "running" | "completed" | "failed";
export type ScrapeSource = "google_maps" | "linkedin";
export type CampaignStatus = "queued" | "running" | "completed" | "failed";

export interface GoogleMapsQueryConfig {
  query: string;
}

export interface LinkedInQueryConfig {
  keywords: string;
  title: string | null;
  company: string | null;
  location: string | null;
}

export type SourceQueryConfig = GoogleMapsQueryConfig | LinkedInQueryConfig;

export interface ScrapeJobSummary {
  id: string;
  campaign_id: string | null;
  query: string;
  query_config: SourceQueryConfig | null;
  source: ScrapeSource;
  max_results: number;
  status: ScrapeJobStatus;
  result_count: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
}

export interface ScrapedLead {
  name: string;
  address: string;
  location: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  headline: string | null;
  current_company: string | null;
  profile_url: string | null;
  reference_link: string | null;
  rating: string | null;
  has_website: boolean;
  source: string;
  scraped_at: string;
}

export interface IntelligenceFactors {
  data_completeness: number;
  business_quality: number;
  digital_presence: number;
  location_value: number;
  industry_potential: number;
  contactability: number;
}

export interface LeadIntelligence {
  score: number;
  category: string;
  priority: string;
  recommendation: string;
  factors: IntelligenceFactors;
}

export interface EnrichedLead extends ScrapedLead {
  intelligence: LeadIntelligence;
}

export interface ScrapeJobResultsResponse {
  job: ScrapeJobSummary;
  results: ScrapedLead[];
}

export interface CreateScrapeJobRequest {
  query: string | null;
  query_config: SourceQueryConfig | null;
  max_results: number;
  source: ScrapeSource;
}

export interface CreateScrapeJobResponse {
  job: ScrapeJobSummary;
}

export interface CreateCampaignRequest {
  name: string;
  industry: string;
  location: string;
  query: string | null;
  query_config: SourceQueryConfig | null;
  max_results: number;
  source: ScrapeSource;
}

export interface CampaignSummary {
  id: string;
  job_id: string;
  name: string;
  industry: string;
  location: string;
  query: string;
  query_config: SourceQueryConfig | null;
  source: ScrapeSource;
  max_results: number;
  status: CampaignStatus;
  total_leads: number;
  average_score: number;
  priority_leads: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
}

export interface CampaignDetail extends CampaignSummary {
  results: EnrichedLead[];
}

export interface CreateCampaignResponse {
  campaign: CampaignSummary;
}

export interface LinkedInSessionStatus {
  source: "linkedin";
  connected: boolean;
  account_label: string | null;
  last_error: string | null;
  updated_at: string | null;
}

export interface ConnectLinkedInSessionRequest {
  username: string;
  password: string;
}

export interface HealthResponse {
  status: string;
  database: {
    path: string;
    healthy: boolean;
  };
  scraper: {
    engine: string;
    timeout_ms: number;
    verify_tls: boolean;
  };
}
