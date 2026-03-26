<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { describeSourceQuery } from "@/lib/sources";
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
const source = computed(() => props.payload?.job.source ?? "google_maps");
const isLinkedIn = computed(() => source.value === "linkedin");

const filteredResults = computed(() => {
  if (!props.payload) {
    return [];
  }

  const needle = filterText.value.trim().toLowerCase();
  if (!needle) {
    return props.payload.results;
  }

  return props.payload.results.filter((lead) =>
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
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle)),
  );
});
const matchCountLabel = computed(() => t("leadTable.matches", { count: filteredResults.value.length }));

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function renderValue(value: string | null | undefined): string {
  return value?.trim() || t("common.unavailable");
}

function getQueryLabel(): string {
  if (!props.payload) {
    return "";
  }

  return props.payload.job.query || describeSourceQuery(props.payload.job.query_config, props.payload.job.source);
}
</script>

<template>
  <section class="panel panel-results">
    <div class="panel-toolbar">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("jobs.resultsKicker") }}</p>
        <h2>{{ t("jobs.resultsTitle") }}</h2>
        <p v-if="payload" class="list-meta">{{ matchCountLabel }}</p>
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
      <InlineStatusNotice
        v-if="payload.job.error_message"
        :title="t('notices.failureTitle')"
        :detail="payload.job.error_message"
        tone="warning"
      />

      <div class="results-summary">
        <div>
          <span class="summary-label">{{ t("jobs.query") }}</span>
          <strong>{{ getQueryLabel() }}</strong>
        </div>
        <div>
          <span class="summary-label">{{ t("jobs.created") }}</span>
          <strong>{{ formatDate(payload.job.created_at) }}</strong>
        </div>
        <div>
          <span class="summary-label">{{ t("jobs.source") }}</span>
          <strong>{{ t(`sources.${payload.job.source}`) }}</strong>
        </div>
        <div>
          <span class="summary-label">{{ t("jobs.leads") }}</span>
          <strong>{{ payload.results.length }}</strong>
        </div>
      </div>

      <div class="panel-toolbar table-toolbar">
        <label class="filter-field table-filter">
          <span>{{ t("leadTable.searchLabel") }}</span>
          <input v-model="filterText" type="search" :placeholder="t('leadTable.searchJobPlaceholder')" />
        </label>
      </div>

      <div v-if="filteredResults.length" class="table-shell">
        <table>
          <thead>
            <tr>
              <th>{{ t("leadTable.columns.lead") }}</th>
              <th>{{ t("leadTable.columns.context") }}</th>
              <th>{{ t("leadTable.columns.contact") }}</th>
              <th>{{ t("leadTable.columns.profile") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="lead in filteredResults"
              :key="`${lead.name}-${lead.profile_url ?? lead.reference_link ?? lead.address}`"
            >
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
                  <a
                    v-if="lead.profile_url"
                    :href="lead.profile_url"
                    target="_blank"
                    rel="noreferrer"
                  >
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
