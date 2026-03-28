import type {
  ActiveLlmConfig,
  CampaignDetail,
  CampaignSummary,
  CreateLlmConfigRequest,
  CreateMailboxRequest,
  ConnectLinkedInSessionRequest,
  CreateSiteRequest,
  DeploySiteResponse,
  CreateCampaignRequest,
  CreateCampaignResponse,
  CreateScrapeJobRequest,
  CreateScrapeJobResponse,
  GenerateEmailsRequest,
  GenerateEmailsResponse,
  HealthResponse,
  LeadEmailHistory,
  LeadOutreachSummary,
  LeadRecipientSummary,
  LinkedInSessionStatus,
  LlmConfigSummary,
  LlmProviderPreset,
  MailFolder,
  MailMessageDetail,
  MailMessageSummary,
  MailProviderConfig,
  MailboxSummary,
  MailboxSyncResponse,
  ScrapeJobResultsResponse,
  ScrapeJobSummary,
  SendMailRequest,
  SendMailResponse,
  SendOutreachEmailsRequest,
  SendOutreachEmailsResponse,
  SiteDeployment,
  SiteSummary,
  UpdateLeadStageRequest,
  UpdateLlmConfigRequest,
  UpdateMailboxRequest,
  UpdateSiteRequest,
} from "@/types";

const API_ROOT = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      // Ignore JSON parsing errors and keep fallback detail.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export const api = {
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },
  listJobs(limit = 50): Promise<ScrapeJobSummary[]> {
    return request<ScrapeJobSummary[]>(`/scrape-jobs?limit=${limit}`);
  },
  getJob(jobId: string): Promise<ScrapeJobSummary> {
    return request<ScrapeJobSummary>(`/scrape-jobs/${jobId}`);
  },
  getJobResults(jobId: string): Promise<ScrapeJobResultsResponse> {
    return request<ScrapeJobResultsResponse>(`/scrape-jobs/${jobId}/results`);
  },
  retryJob(jobId: string): Promise<ScrapeJobSummary> {
    return request<ScrapeJobSummary>(`/scrape-jobs/${jobId}/retry`, {
      method: "POST",
    });
  },
  getLinkedInSession(): Promise<LinkedInSessionStatus> {
    return request<LinkedInSessionStatus>("/linkedin/session");
  },
  connectLinkedInSession(payload: ConnectLinkedInSessionRequest): Promise<LinkedInSessionStatus> {
    return request<LinkedInSessionStatus>("/linkedin/session", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  disconnectLinkedInSession(): Promise<LinkedInSessionStatus> {
    return request<LinkedInSessionStatus>("/linkedin/session", {
      method: "DELETE",
    });
  },
  createJob(payload: CreateScrapeJobRequest): Promise<CreateScrapeJobResponse> {
    return request<CreateScrapeJobResponse>("/scrape-jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listCampaigns(limit = 50): Promise<CampaignSummary[]> {
    return request<CampaignSummary[]>(`/campaigns?limit=${limit}`);
  },
  getCampaign(campaignId: string): Promise<CampaignDetail> {
    return request<CampaignDetail>(`/campaigns/${campaignId}`);
  },
  retryCampaign(campaignId: string): Promise<CampaignSummary> {
    return request<CampaignSummary>(`/campaigns/${campaignId}/retry`, {
      method: "POST",
    });
  },
  createCampaign(payload: CreateCampaignRequest): Promise<CreateCampaignResponse> {
    return request<CreateCampaignResponse>("/campaigns", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listMailProviders(): Promise<MailProviderConfig[]> {
    return request<MailProviderConfig[]>("/mail/providers");
  },
  listMailboxes(): Promise<MailboxSummary[]> {
    return request<MailboxSummary[]>("/mail/mailboxes");
  },
  createMailbox(payload: CreateMailboxRequest): Promise<MailboxSummary> {
    return request<MailboxSummary>("/mail/mailboxes", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateMailbox(mailboxId: string, payload: UpdateMailboxRequest): Promise<MailboxSummary> {
    return request<MailboxSummary>(`/mail/mailboxes/${mailboxId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  syncMailbox(mailboxId: string, limit = 50): Promise<MailboxSyncResponse> {
    return request<MailboxSyncResponse>(`/mail/mailboxes/${mailboxId}/sync?limit=${limit}`, {
      method: "POST",
    });
  },
  listMailMessages(mailboxId: string, folder: MailFolder, limit = 50): Promise<MailMessageSummary[]> {
    return request<MailMessageSummary[]>(
      `/mail/mailboxes/${mailboxId}/messages?folder=${folder}&limit=${limit}`,
    );
  },
  getMailMessage(messageId: string): Promise<MailMessageDetail> {
    return request<MailMessageDetail>(`/mail/messages/${encodeURIComponent(messageId)}`);
  },
  sendMail(payload: SendMailRequest): Promise<SendMailResponse> {
    return request<SendMailResponse>("/mail/send", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listLeadRecipients(limit = 200): Promise<LeadRecipientSummary[]> {
    return request<LeadRecipientSummary[]>(`/mail/lead-recipients?limit=${limit}`);
  },
  // ── LLM Config ────────────────────────────────────────────────────────
  getLlmProviders(): Promise<LlmProviderPreset[]> {
    return request<LlmProviderPreset[]>("/llm/providers");
  },
  listLlmConfigs(): Promise<LlmConfigSummary[]> {
    return request<LlmConfigSummary[]>("/llm/configs");
  },
  createLlmConfig(payload: CreateLlmConfigRequest): Promise<LlmConfigSummary> {
    return request<LlmConfigSummary>("/llm/configs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateLlmConfig(configId: string, payload: UpdateLlmConfigRequest): Promise<LlmConfigSummary> {
    return request<LlmConfigSummary>(`/llm/configs/${configId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteLlmConfig(configId: string): Promise<void> {
    return request<void>(`/llm/configs/${configId}`, {
      method: "DELETE",
    });
  },
  activateLlmConfig(configId: string): Promise<LlmConfigSummary> {
    return request<LlmConfigSummary>(`/llm/configs/${configId}/activate`, {
      method: "POST",
    });
  },
  deactivateLlmConfig(configId: string): Promise<LlmConfigSummary> {
    return request<LlmConfigSummary>(`/llm/configs/${configId}/deactivate`, {
      method: "POST",
    });
  },
  getActiveLlmConfig(): Promise<ActiveLlmConfig | null> {
    return request<ActiveLlmConfig | null>("/llm/configs/active");
  },
  // ── Sites ────────────────────────────────────────────────────────────
  listSites(): Promise<SiteSummary[]> {
    return request<SiteSummary[]>("/sites");
  },
  createSite(payload: CreateSiteRequest): Promise<SiteSummary> {
    return request<SiteSummary>("/sites", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getSite(siteId: string): Promise<SiteSummary> {
    return request<SiteSummary>(`/sites/${siteId}`);
  },
  updateSite(siteId: string, payload: UpdateSiteRequest): Promise<SiteSummary> {
    return request<SiteSummary>(`/sites/${siteId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteSite(siteId: string): Promise<void> {
    return request<void>(`/sites/${siteId}`, { method: "DELETE" });
  },
  deploySite(siteId: string): Promise<DeploySiteResponse> {
    return request<DeploySiteResponse>(`/sites/${siteId}/deploy`, {
      method: "POST",
    });
  },
  listSiteDeployments(siteId: string): Promise<SiteDeployment[]> {
    return request<SiteDeployment[]>(`/sites/${siteId}/deployments`);
  },
  // ── Email Outreach ────────────────────────────────────────────────
  listOutreachLeads(campaignId?: string | null, stage?: number | null): Promise<LeadOutreachSummary[]> {
    const params = new URLSearchParams();
    if (campaignId) params.set("campaign_id", campaignId);
    if (stage != null) params.set("stage", String(stage));
    const qs = params.toString();
    return request<LeadOutreachSummary[]>(`/email-outreach/leads${qs ? `?${qs}` : ""}`);
  },
  updateLeadStage(leadId: string, payload: UpdateLeadStageRequest): Promise<LeadOutreachSummary> {
    return request<LeadOutreachSummary>(`/email-outreach/leads/${leadId}/stage`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  generateEmails(payload: GenerateEmailsRequest): Promise<GenerateEmailsResponse> {
    return request<GenerateEmailsResponse>("/email-outreach/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  sendOutreachEmails(payload: SendOutreachEmailsRequest): Promise<SendOutreachEmailsResponse> {
    return request<SendOutreachEmailsResponse>("/email-outreach/send", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getLeadEmailHistory(leadId: string): Promise<LeadEmailHistory> {
    return request<LeadEmailHistory>(`/email-outreach/history/${leadId}`);
  },
  initCampaignLeadStages(campaignId: string): Promise<{ campaign_id: string; leads_initialized: number }> {
    return request(`/email-outreach/campaigns/${campaignId}/init-stages`, { method: "POST" });
  },
};
