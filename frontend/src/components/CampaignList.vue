<script setup lang="ts">
import { useI18n } from "vue-i18n";

import StatusBadge from "@/components/StatusBadge.vue";
import { describeSourceQuery } from "@/lib/sources";
import type { CampaignStatus, CampaignSummary } from "@/types";

const props = defineProps<{
  campaigns: CampaignSummary[];
  selectedCampaignId: string | null;
  loading: boolean;
  filterQuery: string;
  filterStatus: CampaignStatus | "all";
  totalCampaigns: number;
}>();

const emit = defineEmits<{
  select: [campaignId: string];
  refresh: [];
  updateFilterQuery: [value: string];
  updateFilterStatus: [value: CampaignStatus | "all"];
}>();

const { t } = useI18n();
const statusOptions: Array<CampaignStatus | "all"> = ["all", "queued", "running", "completed", "failed"];

function formatDate(value: string | null): string {
  if (!value) {
    return t("common.notStarted");
  }

  return new Intl.DateTimeFormat("en-GB", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function onFilterQueryInput(event: Event) {
  emit("updateFilterQuery", (event.target as HTMLInputElement).value);
}

function onFilterStatusChange(event: Event) {
  emit("updateFilterStatus", (event.target as HTMLSelectElement).value as CampaignStatus | "all");
}

function getSourceLabel(campaign: CampaignSummary): string {
  return t(`sources.${campaign.source}`);
}

function getQueryLabel(campaign: CampaignSummary): string {
  return campaign.query || describeSourceQuery(campaign.query_config, campaign.source);
}
</script>

<template>
  <section class="panel">
    <div class="panel-toolbar">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("campaigns.queueKicker") }}</p>
        <h2>{{ t("campaigns.queueTitle") }}</h2>
      </div>
      <button class="ghost-button" type="button" @click="$emit('refresh')">
        {{ loading ? `${t("actions.refresh")}...` : t("actions.refresh") }}
      </button>
    </div>

    <div class="inline-filter-grid">
      <label class="filter-field">
        <span>{{ t("filters.searchCampaignsLabel") }}</span>
        <input
          :value="filterQuery"
          type="search"
          :placeholder="t('filters.searchCampaignsPlaceholder')"
          @input="onFilterQueryInput"
        />
      </label>

      <label class="filter-field">
        <span>{{ t("filters.statusLabel") }}</span>
        <select
          :value="filterStatus"
          @change="onFilterStatusChange"
        >
          <option v-for="status in statusOptions" :key="status" :value="status">
            {{ status === "all" ? t("filters.allStatuses") : t(`status.${status}`) }}
          </option>
        </select>
      </label>
    </div>

    <p class="list-meta">{{ t("filters.filteredCount", { visible: props.campaigns.length, total: props.totalCampaigns }) }}</p>

    <div v-if="campaigns.length" class="job-list">
      <button
        v-for="campaign in campaigns"
        :key="campaign.id"
        class="job-card"
        :class="{ selected: campaign.id === selectedCampaignId }"
        type="button"
        @click="$emit('select', campaign.id)"
      >
        <div class="job-card-top">
          <StatusBadge :status="campaign.status" />
          <span class="job-count">{{ getSourceLabel(campaign) }}</span>
        </div>
        <h3>{{ campaign.name }}</h3>
        <p class="job-meta">
          {{ campaign.industry }}
          <span>|</span>
          {{ campaign.location }}
        </p>
        <p class="job-meta">
          {{ formatDate(campaign.created_at) }}
          <span>|</span>
          {{ getQueryLabel(campaign) }}
        </p>
        <p class="job-meta">
          {{ campaign.priority_leads }} {{ t("campaigns.prioritySuffix") }}
          <span>|</span>
          {{ campaign.total_leads }} {{ t("campaigns.leadsSuffix") }}
          <span>|</span>
          {{ campaign.average_score }} {{ t("campaigns.averageScoreSuffix") }}
        </p>
        <p v-if="campaign.error_message" class="job-error">{{ campaign.error_message }}</p>
      </button>
    </div>

    <div v-else class="empty-state">
      <p>{{ totalCampaigns ? t("campaigns.queueFilteredEmptyTitle") : t("campaigns.queueEmptyTitle") }}</p>
      <span>{{ totalCampaigns ? t("campaigns.queueFilteredEmptyDescription") : t("campaigns.queueEmptyDescription") }}</span>
    </div>
  </section>
</template>
