<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import StatusBadge from "@/components/StatusBadge.vue";
import type { ScrapeJobResultsResponse, ScrapedLead } from "@/types";

const props = defineProps<{
  payload: ScrapeJobResultsResponse | null;
  loading: boolean;
  retrying: boolean;
}>();
const emit = defineEmits<{
  export: [leads: ScrapedLead[]];
  retry: [jobId: string];
}>();

const filterText = ref("");
const { t } = useI18n();

const filteredResults = computed(() => {
  if (!props.payload) {
    return [];
  }

  const needle = filterText.value.trim().toLowerCase();
  if (!needle) {
    return props.payload.results;
  }

  return props.payload.results.filter((lead) =>
    [lead.name, lead.address, lead.phone, lead.email, lead.website]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle)),
  );
});

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
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
  <section class="panel panel-results">
    <div class="panel-toolbar">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("jobs.resultsKicker") }}</p>
        <h2>{{ t("jobs.resultsTitle") }}</h2>
      </div>
      <div class="panel-actions">
        <button
          v-if="payload?.job.status === 'failed'"
          class="ghost-button"
          type="button"
          :disabled="retrying"
          @click="emit('retry', payload.job.id)"
        >
          {{ retrying ? t("actions.retrying") : t("actions.retry") }}
        </button>
        <button
          v-if="payload"
          class="ghost-button"
          type="button"
          @click="emit('export', filteredResults)"
        >
          {{ t("actions.exportLeads") }}
        </button>
        <StatusBadge v-if="payload" :status="payload.job.status" />
      </div>
    </div>

    <template v-if="payload">
      <div class="results-summary">
        <div>
          <span class="summary-label">{{ t("jobs.query") }}</span>
          <strong>{{ payload.job.query }}</strong>
        </div>
        <div>
          <span class="summary-label">{{ t("jobs.created") }}</span>
          <strong>{{ formatDate(payload.job.created_at) }}</strong>
        </div>
        <div>
          <span class="summary-label">{{ t("jobs.leads") }}</span>
          <strong>{{ payload.results.length }}</strong>
        </div>
      </div>

      <label class="filter-field">
        <span>{{ t("leadTable.searchLabel") }}</span>
        <input v-model="filterText" type="search" :placeholder="t('leadTable.searchJobPlaceholder')" />
      </label>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>{{ t("leadTable.columns.business") }}</th>
              <th>{{ t("leadTable.columns.address") }}</th>
              <th>{{ t("leadTable.columns.phone") }}</th>
              <th>{{ t("leadTable.columns.email") }}</th>
              <th>{{ t("leadTable.columns.rating") }}</th>
              <th>{{ t("leadTable.columns.website") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in filteredResults" :key="`${lead.name}-${lead.address}`">
              <td>{{ lead.name }}</td>
              <td>{{ lead.address }}</td>
              <td>{{ lead.phone || "-" }}</td>
              <td>{{ lead.email || t("common.unavailable") }}</td>
              <td>{{ lead.rating || "-" }}</td>
              <td>
                <a v-if="lead.website" :href="lead.website" target="_blank" rel="noreferrer">
                  {{ t("common.visit") }}
                </a>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>{{ t("leadTable.emptyTitle") }}</p>
        <span>{{ t("leadTable.emptyDescription") }}</span>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>{{ loading ? t("common.loadingJob") : t("common.noJobSelected") }}</p>
      <span>{{ t("leadTable.noJobDescription") }}</span>
    </div>
  </section>
</template>
