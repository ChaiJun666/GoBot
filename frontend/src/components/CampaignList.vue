<script setup lang="ts">
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

function formatDate(value: string | null): string {
  if (!value) {
    return "Not started";
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
        <p class="panel-kicker">Pipeline</p>
        <h2>Campaign queue</h2>
      </div>
      <button class="ghost-button" @click="$emit('refresh')">
        {{ loading ? "Refreshing..." : "Refresh" }}
      </button>
    </div>

    <div v-if="campaigns.length" class="job-list">
      <button
        v-for="campaign in campaigns"
        :key="campaign.id"
        class="job-card"
        :class="{ selected: campaign.id === selectedCampaignId }"
        @click="$emit('select', campaign.id)"
      >
        <div class="job-card-top">
          <StatusBadge :status="campaign.status" />
          <span class="job-count">{{ campaign.priority_leads }} priority</span>
        </div>
        <h3>{{ campaign.name }}</h3>
        <p class="job-meta">
          {{ campaign.industry }}
          <span>·</span>
          {{ campaign.location }}
          <span>·</span>
          {{ formatDate(campaign.created_at) }}
        </p>
        <p class="job-meta">
          {{ campaign.total_leads }} leads
          <span>·</span>
          {{ campaign.average_score }} avg score
        </p>
        <p v-if="campaign.error_message" class="job-error">{{ campaign.error_message }}</p>
      </button>
    </div>

    <div v-else class="empty-state">
      <p>No campaigns yet.</p>
      <span>Create a campaign to combine scrape execution and intelligence scoring.</span>
    </div>
  </section>
</template>
