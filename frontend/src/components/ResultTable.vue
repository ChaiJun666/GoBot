<script setup lang="ts">
import { computed, ref } from "vue";

import StatusBadge from "@/components/StatusBadge.vue";
import type { ScrapeJobResultsResponse } from "@/types";

const props = defineProps<{
  payload: ScrapeJobResultsResponse | null;
  loading: boolean;
}>();

const filterText = ref("");

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
        <p class="panel-kicker">Inspect</p>
        <h2>Results</h2>
      </div>
      <StatusBadge v-if="payload" :status="payload.job.status" />
    </div>

    <template v-if="payload">
      <div class="results-summary">
        <div>
          <span class="summary-label">Query</span>
          <strong>{{ payload.job.query }}</strong>
        </div>
        <div>
          <span class="summary-label">Created</span>
          <strong>{{ formatDate(payload.job.created_at) }}</strong>
        </div>
        <div>
          <span class="summary-label">Leads</span>
          <strong>{{ payload.results.length }}</strong>
        </div>
      </div>

      <label class="filter-field">
        <span>Filter leads</span>
        <input v-model="filterText" type="search" placeholder="Search name, address, phone, website" />
      </label>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Address</th>
              <th>Phone</th>
              <th>Rating</th>
              <th>Website</th>
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
                  Visit
                </a>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>No matching leads.</p>
        <span>Try a different filter or wait for the job to complete.</span>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>{{ loading ? "Loading job..." : "No job selected." }}</p>
      <span>Select a job from the queue to inspect its leads.</span>
    </div>
  </section>
</template>
