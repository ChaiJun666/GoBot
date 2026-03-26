<script setup lang="ts">
import { useI18n } from "vue-i18n";

import StatusBadge from "@/components/StatusBadge.vue";
import type { CampaignSummary } from "@/types";

defineProps<{
  campaigns: CampaignSummary[];
  selectedCampaignId: string | null;
  loading: boolean;
}>();

defineEmits<{
  select: [campaignId: string];
  refresh: [];
}>();

const { t } = useI18n();

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
          <span class="job-count">{{ campaign.priority_leads }} {{ t("campaigns.prioritySuffix") }}</span>
        </div>
        <h3>{{ campaign.name }}</h3>
        <p class="job-meta">
          {{ campaign.industry }}
          <span>|</span>
          {{ campaign.location }}
          <span>|</span>
          {{ formatDate(campaign.created_at) }}
        </p>
        <p class="job-meta">
          {{ campaign.total_leads }} {{ t("campaigns.leadsSuffix") }}
          <span>|</span>
          {{ campaign.average_score }} {{ t("campaigns.averageScoreSuffix") }}
        </p>
        <p v-if="campaign.error_message" class="job-error">{{ campaign.error_message }}</p>
      </button>
    </div>

    <div v-else class="empty-state">
      <p>{{ t("campaigns.queueEmptyTitle") }}</p>
      <span>{{ t("campaigns.queueEmptyDescription") }}</span>
    </div>
  </section>
</template>
