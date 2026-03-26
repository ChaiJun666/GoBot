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

export type MailboxStatus = "ready" | "error";
export type MailFolder = "inbox" | "sent";
export type MailProviderKey =
  | "163.com"
  | "vip.163.com"
  | "126.com"
  | "vip.126.com"
  | "188.com"
  | "vip.188.com"
  | "yeah.net"
  | "gmail"
  | "outlook"
  | "qq";

export interface MailProviderConfig {
  key: MailProviderKey;
  label: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_starttls: boolean;
}

export interface MailboxSummary {
  id: string;
  provider: MailProviderKey;
  email_address: string;
  note: string | null;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_starttls: boolean;
  status: MailboxStatus;
  last_error: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateMailboxRequest {
  provider: MailProviderKey;
  email_address: string;
  auth_secret: string;
  note: string | null;
}

export interface UpdateMailboxRequest {
  note: string | null;
  auth_secret?: string | null;
}

export interface MailboxSyncResponse {
  mailbox: MailboxSummary;
  inbox_count: number;
  sent_count: number;
}

export interface MailMessageSummary {
  id: string;
  mailbox_id: string;
  folder: MailFolder;
  remote_uid: string;
  message_id: string | null;
  subject: string;
  from_name: string | null;
  from_address: string | null;
  to_summary: string | null;
  snippet: string | null;
  is_read: boolean;
  sent_at: string | null;
  received_at: string | null;
  synced_at: string;
}

export interface MailMessageDetail extends MailMessageSummary {
  body_text: string | null;
}

export interface SendMailRequest {
  mailbox_id: string;
  to: string[];
  subject: string;
  body: string;
}

export interface SendMailResponse {
  mailbox: MailboxSummary;
  accepted: string[];
  message: string;
}

export interface LeadRecipientSummary {
  id: string;
  email: string;
  lead_name: string;
  campaign_id: string;
  campaign_name: string;
  source: string;
  company: string | null;
}
