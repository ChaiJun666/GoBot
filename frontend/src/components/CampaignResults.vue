<script setup lang="ts">
import { computed, ref } from "vue";

import StatusBadge from "@/components/StatusBadge.vue";
import type { CampaignDetail } from "@/types";

const props = defineProps<{
  campaign: CampaignDetail | null;
  loading: boolean;
}>();

const filterText = ref("");

const filteredResults = computed(() => {
  if (!props.campaign) {
    return [];
  }

  const needle = filterText.value.trim().toLowerCase();
  if (!needle) {
    return props.campaign.results;
  }

  return props.campaign.results.filter((lead) =>
    [
      lead.name,
      lead.address,
      lead.phone,
      lead.website,
      lead.intelligence.priority,
      lead.intelligence.category,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle)),
  );
});
</script>

<template>
  <section class="panel panel-results">
    <div class="panel-toolbar">
      <div class="panel-heading">
        <p class="panel-kicker">Intelligence</p>
        <h2>Campaign leads</h2>
      </div>
      <StatusBadge v-if="campaign" :status="campaign.status" />
    </div>

    <template v-if="campaign">
      <div class="results-summary">
        <div>
          <span class="summary-label">Campaign</span>
          <strong>{{ campaign.name }}</strong>
        </div>
        <div>
          <span class="summary-label">Priority leads</span>
          <strong>{{ campaign.priority_leads }}</strong>
        </div>
        <div>
          <span class="summary-label">Average score</span>
          <strong>{{ campaign.average_score }}</strong>
        </div>
      </div>

      <label class="filter-field">
        <span>Filter leads</span>
        <input
          v-model="filterText"
          type="search"
          placeholder="Search business, location, priority, category"
        />
      </label>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Priority</th>
              <th>Score</th>
              <th>Category</th>
              <th>Phone</th>
              <th>Website</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in filteredResults" :key="`${lead.name}-${lead.address}`">
              <td>
                <strong>{{ lead.name }}</strong>
                <div class="subcell">{{ lead.address }}</div>
              </td>
              <td>{{ lead.intelligence.priority }}</td>
              <td>{{ lead.intelligence.score }}</td>
              <td>{{ lead.intelligence.category }}</td>
              <td>{{ lead.phone || "-" }}</td>
              <td>
                <a v-if="lead.website" :href="lead.website" target="_blank" rel="noreferrer">Visit</a>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>No matching leads.</p>
        <span>Try a different filter or wait for the campaign to finish processing.</span>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>{{ loading ? "Loading campaign..." : "No campaign selected." }}</p>
      <span>Select a campaign to inspect intelligence-scored leads.</span>
    </div>
  </section>
</template>
