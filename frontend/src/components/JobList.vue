<script setup lang="ts">
import StatusBadge from "@/components/StatusBadge.vue";
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
        <p class="panel-kicker">Queue</p>
        <h2>Recent jobs</h2>
      </div>
      <button class="ghost-button" @click="$emit('refresh')">
        {{ loading ? "Refreshing..." : "Refresh" }}
      </button>
    </div>

    <div v-if="jobs.length" class="job-list">
      <button
        v-for="job in jobs"
        :key="job.id"
        class="job-card"
        :class="{ selected: job.id === selectedJobId }"
        @click="$emit('select', job.id)"
      >
        <div class="job-card-top">
          <StatusBadge :status="job.status" />
          <span class="job-count">{{ job.result_count }} leads</span>
        </div>
        <h3>{{ job.query }}</h3>
        <p class="job-meta">
          {{ formatDate(job.created_at) }}
          <span>·</span>
          {{ job.max_results }} requested
        </p>
        <p v-if="job.error_message" class="job-error">{{ job.error_message }}</p>
      </button>
    </div>

    <div v-else class="empty-state">
      <p>No jobs yet.</p>
      <span>Launch a scrape run to populate the console.</span>
    </div>
  </section>
</template>
