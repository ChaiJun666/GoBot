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
  id: string;
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

export interface MailMessageCountResponse {
  folder: MailFolder;
  count: number;
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

// ── LLM Config ────────────────────────────────────────────────────────

export type LlmProviderKey = "openai" | "xai" | "anthropic" | "deepseek" | "qwen" | "zhipu" | "minimax";

export interface LlmProviderPreset {
  key: LlmProviderKey;
  display_name: string;
  default_base_url: string;
  official_url: string;
}

export interface LlmConfigSummary {
  id: string;
  provider: string;
  display_name: string;
  model_name: string;
  base_url: string;
  official_url: string | null;
  note: string | null;
  has_api_key: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateLlmConfigRequest {
  provider: LlmProviderKey;
  display_name: string;
  model_name: string;
  base_url: string;
  api_key: string;
  note: string | null;
  official_url: string | null;
}

export interface UpdateLlmConfigRequest {
  display_name?: string | null;
  model_name?: string | null;
  base_url?: string | null;
  api_key?: string | null;
  note?: string | null;
  official_url?: string | null;
}

export interface ActiveLlmConfig {
  id: string;
  provider: string;
  display_name: string;
  model_name: string;
  base_url: string;
  official_url: string | null;
  note: string | null;
  api_key: string;
  created_at: string;
  updated_at: string;
}

// ── Sites ────────────────────────────────────────────────────────────

export type SiteStatus = "draft" | "deploying" | "running" | "stopped" | "error";
export type SslMode = "none" | "letsencrypt" | "cloudflare";

export interface SiteSummary {
  id: string;
  display_name: string;
  slug: string;
  domain: string;
  server_ip: string;
  ssh_user: string;
  has_ssh_password: boolean;
  wp_admin_user: string;
  has_wp_admin_password: boolean;
  wp_admin_email: string;
  mysql_database: string;
  mysql_user: string;
  has_mysql_password: boolean;
  ssl_mode: SslMode;
  cloudflare_zone_id: string | null;
  has_cloudflare_api_token: boolean;
  cloudflare_dns_proxy: boolean;
  wp_plugins: string[];
  status: SiteStatus;
  deploy_log: string | null;
  site_url: string | null;
  wp_admin_url: string | null;
  deployed_at: string | null;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSiteRequest {
  display_name: string;
  domain: string;
  server_ip: string;
  ssh_user: string;
  ssh_password: string;
  wp_admin_email: string;
  mysql_root_password: string;
  slug?: string | null;
  wp_admin_user?: string | null;
  wp_admin_password?: string | null;
  mysql_database?: string | null;
  mysql_user?: string | null;
  mysql_password?: string | null;
  ssl_mode?: SslMode | null;
  cloudflare_zone_id?: string | null;
  cloudflare_api_token?: string | null;
  cloudflare_dns_proxy?: boolean | null;
  wp_plugins?: string[] | null;
  note?: string | null;
}

export interface UpdateSiteRequest {
  display_name?: string | null;
  domain?: string | null;
  server_ip?: string | null;
  ssh_user?: string | null;
  ssh_password?: string | null;
  wp_admin_user?: string | null;
  wp_admin_password?: string | null;
  wp_admin_email?: string | null;
  mysql_root_password?: string | null;
  mysql_database?: string | null;
  mysql_user?: string | null;
  mysql_password?: string | null;
  ssl_mode?: SslMode | null;
  cloudflare_zone_id?: string | null;
  cloudflare_api_token?: string | null;
  cloudflare_dns_proxy?: boolean | null;
  wp_plugins?: string[] | null;
  note?: string | null;
}

export interface SiteDeployment {
  id: string;
  site_id: string;
  status: "pending" | "running" | "completed" | "failed";
  log: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface DeploySiteResponse {
  site: SiteSummary;
  deployment: SiteDeployment;
}

// ── Email Outreach ──────────────────────────────────────────────────

export type OutreachLanguage = "auto" | "en" | "zh";

export interface LeadOutreachSummary {
  id: string;
  lead_id: string;
  lead_email: string;
  lead_name: string;
  lead_company: string | null;
  lead_industry: string | null;
  lead_location: string | null;
  lead_source: string | null;
  lead_headline: string | null;
  campaign_id: string;
  campaign_name: string | null;
  current_stage: number;
  emails_sent: number;
  last_email_at: string | null;
  next_stage_at: string | null;
  language: OutreachLanguage;
  manual_override: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateLeadStageRequest {
  stage: number;
  manual_override: boolean;
}

export interface GenerateEmailsRequest {
  lead_ids: string[];
  stage?: number | null;
  language?: OutreachLanguage | null;
  user_instructions?: string | null;
}

export interface GeneratedEmail {
  lead_id: string;
  subject: string;
  body: string;
}

export interface GenerateEmailsResponse {
  emails: GeneratedEmail[];
  errors: { lead_id: string; error: string }[];
}

export interface OutreachSendEmailItem {
  lead_id: string;
  mailbox_id: string;
  subject: string;
  body: string;
}

export interface SendOutreachEmailsRequest {
  emails: OutreachSendEmailItem[];
}

export interface SendOutreachEmailResult {
  lead_id: string;
  status: "sent" | "error";
  error: string | null;
}

export interface SendOutreachEmailsResponse {
  results: SendOutreachEmailResult[];
}

export interface LeadEmailHistory {
  lead_id: string;
  lead_name: string;
  messages: MailMessageSummary[];
}
