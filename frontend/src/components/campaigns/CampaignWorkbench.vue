<script setup lang="ts">
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import LeadInspectorTable from "@/components/campaigns/LeadInspectorTable.vue";
import { describeSourceQuery } from "@/lib/sources";
import type { CampaignDetail, EnrichedLead, ScrapeJobSummary } from "@/types";

defineProps<{
  campaign: CampaignDetail | null;
  linkedJob: ScrapeJobSummary | null;
  loading: boolean;
  retrying: boolean;
}>();
const emit = defineEmits<{
  retry: [campaignId: string];
  export: [leads: EnrichedLead[]];
}>();

const { t } = useI18n();

function getQueryLabel(
  value: Pick<CampaignDetail, "query" | "query_config" | "source"> | Pick<ScrapeJobSummary, "query" | "query_config" | "source">,
): string {
  return value.query || describeSourceQuery(value.query_config, value.source);
}

function formatDate(value: string | null): string {
  if (!value) {
    return t("common.pending");
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
</script>

<template>
  <section class="campaign-workbench">
    <section class="panel panel-detail">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("campaigns.selectedKicker") }}</p>
          <h2>{{ campaign ? campaign.name : t("campaigns.workbenchTitle") }}</h2>
        </div>
        <div class="panel-actions">
          <button
            v-if="campaign?.status === 'failed'"
            class="ghost-button"
            type="button"
            :disabled="retrying"
            @click="emit('retry', campaign.id)"
          >
            {{ retrying ? t("actions.retrying") : t("actions.retry") }}
          </button>
          <StatusBadge v-if="campaign" :status="campaign.status" />
        </div>
      </div>

      <template v-if="campaign">
        <InlineStatusNotice
          v-if="campaign.error_message"
          :title="t('notices.failureTitle')"
          :detail="campaign.error_message"
          tone="warning"
        />

        <div class="results-summary">
          <div>
            <span class="summary-label">{{ t("campaigns.detail.priorityLeads") }}</span>
            <strong>{{ campaign.priority_leads }}</strong>
          </div>
          <div>
            <span class="summary-label">{{ t("campaigns.detail.averageScore") }}</span>
            <strong>{{ campaign.average_score }}</strong>
          </div>
          <div>
            <span class="summary-label">{{ t("campaigns.detail.totalLeads") }}</span>
            <strong>{{ campaign.total_leads }}</strong>
          </div>
        </div>

        <dl class="detail-grid">
          <div>
            <dt>{{ t("campaigns.detail.source") }}</dt>
            <dd>{{ t(`sources.${campaign.source}`) }}</dd>
          </div>
          <div>
            <dt>{{ t("campaigns.detail.industry") }}</dt>
            <dd>{{ campaign.industry }}</dd>
          </div>
          <div>
            <dt>{{ t("campaigns.detail.location") }}</dt>
            <dd>{{ campaign.location }}</dd>
          </div>
          <div>
            <dt>{{ t("campaigns.detail.query") }}</dt>
            <dd>{{ getQueryLabel(campaign) }}</dd>
          </div>
          <div>
            <dt>{{ t("campaigns.detail.jobId") }}</dt>
            <dd>{{ campaign.job_id }}</dd>
          </div>
          <div>
            <dt>{{ t("jobs.created") }}</dt>
            <dd>{{ formatDate(campaign.created_at) }}</dd>
          </div>
          <div>
            <dt>{{ t("jobs.completed") }}</dt>
            <dd>{{ formatDate(campaign.completed_at) }}</dd>
          </div>
        </dl>
      </template>
      <div v-else class="empty-state compact-empty">
        <p>{{ loading ? t("common.loadingCampaign") : t("common.noCampaignSelected") }}</p>
        <span>{{ t("campaigns.emptyWorkbenchDescription") }}</span>
      </div>
    </section>

    <LeadInspectorTable :campaign="campaign" :loading="loading" @export="emit('export', $event)" />

    <details class="panel panel-detail telemetry-disclosure" :open="Boolean(linkedJob && campaign)">
      <summary>{{ t("campaigns.telemetryTitle") }}</summary>
      <InlineStatusNotice
        v-if="linkedJob?.error_message"
        :title="t('notices.failureTitle')"
        :detail="linkedJob.error_message"
        tone="warning"
      />
      <dl v-if="linkedJob" class="detail-grid">
        <div>
          <dt>{{ t("campaigns.detail.jobId") }}</dt>
          <dd>{{ linkedJob.id }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.campaignLink") }}</dt>
          <dd>{{ linkedJob.campaign_id ?? t("common.unlinked") }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.source") }}</dt>
          <dd>{{ t(`sources.${linkedJob.source}`) }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.created") }}</dt>
          <dd>{{ formatDate(linkedJob.created_at) }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.completed") }}</dt>
          <dd>{{ formatDate(linkedJob.completed_at) }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.query") }}</dt>
          <dd>{{ getQueryLabel(linkedJob) }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.returned") }}</dt>
          <dd>{{ linkedJob.result_count }}</dd>
        </div>
        <div>
          <dt>{{ t("jobs.requested") }}</dt>
          <dd>{{ linkedJob.max_results }}</dd>
        </div>
      </dl>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("common.noLinkedJobSelected") }}</p>
        <span>{{ t("campaigns.telemetryEmptyDescription") }}</span>
      </div>
    </details>
  </section>
</template>
