<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import type { CampaignDetail, EnrichedLead } from "@/types";

const props = defineProps<{
  campaign: CampaignDetail | null;
  loading: boolean;
}>();
const emit = defineEmits<{
  export: [leads: EnrichedLead[]];
}>();

const filterText = ref("");
const { t } = useI18n();

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
    <div class="panel-heading">
      <p class="panel-kicker">{{ t("campaigns.leadReviewKicker") }}</p>
      <h2>{{ t("campaigns.leadReviewTitle") }}</h2>
    </div>

    <template v-if="campaign">
      <label class="filter-field">
        <span>{{ t("leadTable.searchLabel") }}</span>
        <input
          v-model="filterText"
          type="search"
          :placeholder="t('leadTable.searchCampaignPlaceholder')"
        />
      </label>

      <div class="panel-actions">
        <button class="ghost-button" type="button" @click="emit('export', filteredResults)">
          {{ t("actions.exportLeads") }}
        </button>
      </div>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>{{ t("leadTable.columns.business") }}</th>
              <th>{{ t("leadTable.columns.priority") }}</th>
              <th>{{ t("leadTable.columns.score") }}</th>
              <th>{{ t("leadTable.columns.category") }}</th>
              <th>{{ t("leadTable.columns.phone") }}</th>
              <th>{{ t("leadTable.columns.email") }}</th>
              <th>{{ t("leadTable.columns.website") }}</th>
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
              <td>{{ lead.email || t("common.unavailable") }}</td>
              <td>
                <a v-if="lead.website" :href="lead.website" target="_blank" rel="noreferrer">{{ t("common.visit") }}</a>
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
      <p>{{ loading ? t("common.loadingCampaign") : t("common.noCampaignSelected") }}</p>
      <span>{{ t("leadTable.noCampaignDescription") }}</span>
    </div>
  </section>
</template>
