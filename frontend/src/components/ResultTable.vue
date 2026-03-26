<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import StatusBadge from "@/components/StatusBadge.vue";
import type { ScrapeJobResultsResponse } from "@/types";

const props = defineProps<{
  payload: ScrapeJobResultsResponse | null;
  loading: boolean;
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
    [lead.name, lead.address, lead.phone, lead.website]
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
      <StatusBadge v-if="payload" :status="payload.job.status" />
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
        <span>{{ t("jobs.filterLeads") }}</span>
        <input v-model="filterText" type="search" :placeholder="t('jobs.filterPlaceholder')" />
      </label>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>{{ t("jobs.table.name") }}</th>
              <th>{{ t("jobs.table.address") }}</th>
              <th>{{ t("jobs.table.phone") }}</th>
              <th>{{ t("jobs.table.rating") }}</th>
              <th>{{ t("jobs.table.website") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in filteredResults" :key="`${lead.name}-${lead.address}`">
              <td>{{ lead.name }}</td>
              <td>{{ lead.address }}</td>
              <td>{{ lead.phone || "-" }}</td>
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
        <p>{{ t("jobs.emptyFilteredTitle") }}</p>
        <span>{{ t("jobs.emptyFilteredDescription") }}</span>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>{{ loading ? t("common.loadingJob") : t("common.noJobSelected") }}</p>
      <span>{{ t("jobs.emptyResultsDescription") }}</span>
    </div>
  </section>
</template>
