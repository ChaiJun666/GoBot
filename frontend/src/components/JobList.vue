<script setup lang="ts">
import { useI18n } from "vue-i18n";

import StatusBadge from "@/components/StatusBadge.vue";
import { describeSourceQuery } from "@/lib/sources";
import type { ScrapeJobSummary } from "@/types";

defineProps<{
  jobs: ScrapeJobSummary[];
  selectedJobId: string | null;
  loading: boolean;
}>();

defineEmits<{
  select: [jobId: string];
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

function getSourceLabel(job: ScrapeJobSummary): string {
  return t(`sources.${job.source}`);
}

function getQueryLabel(job: ScrapeJobSummary): string {
  return job.query || describeSourceQuery(job.query_config, job.source);
}
</script>

<template>
  <section class="panel">
    <div class="panel-toolbar">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("jobs.queueKicker") }}</p>
        <h2>{{ t("jobs.queueTitle") }}</h2>
      </div>
      <button class="ghost-button" type="button" @click="$emit('refresh')">
        {{ loading ? `${t("actions.refresh")}...` : t("actions.refresh") }}
      </button>
    </div>

    <div v-if="jobs.length" class="job-list">
      <button
        v-for="job in jobs"
        :key="job.id"
        class="job-card"
        :class="{ selected: job.id === selectedJobId }"
        type="button"
        @click="$emit('select', job.id)"
      >
        <div class="job-card-top">
          <StatusBadge :status="job.status" />
          <span class="job-count">{{ getSourceLabel(job) }}</span>
        </div>
        <h3>{{ getQueryLabel(job) }}</h3>
        <p class="job-meta">
          {{ formatDate(job.created_at) }}
          <span>|</span>
          {{ job.max_results }} {{ t("jobs.requestedSuffix") }}
        </p>
        <p class="job-meta">{{ job.result_count }} {{ t("jobs.leadsSuffix") }}</p>
        <p v-if="job.error_message" class="job-error">{{ job.error_message }}</p>
      </button>
    </div>

    <div v-else class="empty-state">
      <p>{{ t("jobs.queueEmptyTitle") }}</p>
      <span>{{ t("jobs.queueEmptyDescription") }}</span>
    </div>
  </section>
</template>
