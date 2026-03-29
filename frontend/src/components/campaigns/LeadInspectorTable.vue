<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import LeadEditDrawer from "@/components/campaigns/LeadEditDrawer.vue";
import type { CampaignDetail, EnrichedLead } from "@/types";

const props = defineProps<{
  campaign: CampaignDetail | null;
  loading: boolean;
}>();
const emit = defineEmits<{
  export: [leads: EnrichedLead[]];
  editLead: [campaignId: string, leadId: string, updates: Record<string, string | null>];
  deleteLead: [campaignId: string, leadId: string];
}>();

const filterText = ref("");
const editingLead = ref<EnrichedLead | null>(null);
const deletingLeadId = ref<string | null>(null);
const { t } = useI18n();
const source = computed(() => props.campaign?.source ?? "google_maps");
const isLinkedIn = computed(() => source.value === "linkedin");

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
      lead.location,
      lead.phone,
      lead.email,
      lead.website,
      lead.headline,
      lead.current_company,
      lead.profile_url,
      lead.reference_link,
      lead.rating,
      lead.intelligence.priority,
      lead.intelligence.category,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle)),
  );
});
const matchCountLabel = computed(() => t("leadTable.matches", { count: filteredResults.value.length }));

function renderValue(value: string | null | undefined): string {
  return value?.trim() || t("common.unavailable");
}

function handleEditSave(leadId: string, updates: Record<string, string | null>) {
  if (!props.campaign) return;
  emit("editLead", props.campaign.id, leadId, updates);
  editingLead.value = null;
}

function confirmDelete() {
  if (!deletingLeadId.value || !props.campaign) return;
  emit("deleteLead", props.campaign.id, deletingLeadId.value);
  deletingLeadId.value = null;
}
</script>

<template>
  <section class="panel panel-results">
    <div class="panel-heading">
      <p class="panel-kicker">{{ t("campaigns.leadReviewKicker") }}</p>
      <h2>{{ t("campaigns.leadReviewTitle") }}</h2>
      <p v-if="campaign" class="list-meta">{{ matchCountLabel }}</p>
    </div>

    <template v-if="campaign">
      <div class="panel-toolbar table-toolbar">
        <label class="filter-field table-filter">
          <span>{{ t("leadTable.searchLabel") }}</span>
          <input
            v-model="filterText"
            type="search"
            :placeholder="t('leadTable.searchCampaignPlaceholder')"
          />
        </label>

        <button class="ghost-button" type="button" @click="emit('export', filteredResults)">
          {{ t("actions.exportLeads") }}
        </button>
      </div>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>{{ t("leadTable.columns.lead") }}</th>
              <th>{{ t("leadTable.columns.priority") }}</th>
              <th>{{ t("leadTable.columns.score") }}</th>
              <th>{{ t("leadTable.columns.category") }}</th>
              <th>{{ t("leadTable.columns.context") }}</th>
              <th>{{ t("leadTable.columns.contact") }}</th>
              <th>{{ t("leadTable.columns.profile") }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="lead in filteredResults" :key="lead.id">
              <tr v-if="deletingLeadId === lead.id" class="row-deleting">
                <td colspan="7">
                  <div class="inline-confirm">
                    <span class="inline-confirm-text">{{ t("leadTable.deleteConfirmTitle") }} <strong>{{ lead.name }}</strong></span>
                    <div class="inline-confirm-actions">
                      <button class="action-button" type="button" style="font-size:0.7rem;padding:0.15rem 0.5rem"
                        @click="confirmDelete">{{ t("leadTable.confirmDelete") }}</button>
                      <button class="ghost-button" type="button" style="font-size:0.7rem;padding:0.15rem 0.5rem"
                        @click="deletingLeadId = null">{{ t("leadTable.cancelDelete") }}</button>
                    </div>
                  </div>
                </td>
              </tr>
              <tr v-else>
              <td>
                <strong>{{ lead.name }}</strong>
                <div class="subcell">
                  {{
                    isLinkedIn
                      ? renderValue(lead.headline || lead.location)
                      : renderValue(lead.address)
                  }}
                </div>
              </td>
              <td>{{ lead.intelligence.priority }}</td>
              <td>{{ lead.intelligence.score }}</td>
              <td>{{ lead.intelligence.category }}</td>
              <td>
                <div v-if="isLinkedIn">
                  <div class="subcell">
                    {{ t("leadTable.details.company") }}: {{ renderValue(lead.current_company) }}
                  </div>
                  <div class="subcell">
                    {{ t("leadTable.details.location") }}: {{ renderValue(lead.location) }}
                  </div>
                </div>
                <div v-else>
                  <div class="subcell">
                    {{ t("leadTable.details.address") }}: {{ renderValue(lead.address) }}
                  </div>
                  <div class="subcell">
                    {{ t("leadTable.details.rating") }}: {{ renderValue(lead.rating) }}
                  </div>
                </div>
              </td>
              <td>
                <div class="subcell">
                  {{ t("leadTable.details.phone") }}: {{ renderValue(lead.phone) }}
                </div>
                <div class="subcell">
                  {{ t("leadTable.details.email") }}: {{ renderValue(lead.email) }}
                </div>
              </td>
              <td>
                <div v-if="isLinkedIn">
                  <a v-if="lead.profile_url" :href="lead.profile_url" target="_blank" rel="noreferrer">
                    {{ t("leadTable.details.profileUrl") }}
                  </a>
                  <span v-else>{{ t("common.unavailable") }}</span>
                </div>
                <div v-else>
                  <a v-if="lead.website" :href="lead.website" target="_blank" rel="noreferrer">
                    {{ t("leadTable.details.website") }}
                  </a>
                  <span v-else>{{ t("common.unavailable") }}</span>
                </div>
                <div v-if="lead.reference_link" class="subcell">
                  <a :href="lead.reference_link" target="_blank" rel="noreferrer">
                    {{ t("leadTable.details.sourceLink") }}
                  </a>
                </div>
                <div class="subcell lead-actions">
                  <button class="ghost-button" type="button" style="font-size:0.7rem;padding:0.15rem 0.4rem"
                    @click="editingLead = lead">{{ t("leadTable.editLead") }}</button>
                  <button class="ghost-button" type="button" style="font-size:0.7rem;padding:0.15rem 0.4rem;color:var(--color-danger)"
                    @click="deletingLeadId = lead.id">{{ t("leadTable.deleteLead") }}</button>
                </div>
              </td>
            </tr>
            </template>
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

    <LeadEditDrawer
      :open="Boolean(editingLead)"
      :lead="editingLead"
      @save="handleEditSave"
      @cancel="editingLead = null"
    />
  </section>
</template>

<style scoped>
.lead-actions { display: flex; gap: 0.25rem; margin-top: 0.25rem; }
.row-deleting { background: color-mix(in srgb, var(--color-danger) 8%, transparent); }
.row-deleting td { padding: 0.5rem 0.75rem; }
.inline-confirm { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; }
.inline-confirm-text { font-size: 0.85rem; }
.inline-confirm-actions { display: flex; gap: 0.35rem; }
</style>
