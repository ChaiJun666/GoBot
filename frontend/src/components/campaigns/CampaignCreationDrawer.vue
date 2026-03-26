<script setup lang="ts">
import { computed, reactive } from "vue";
import { useI18n } from "vue-i18n";

import { buildLinkedInQuerySummary } from "@/lib/sources";
import type { CreateCampaignRequest, LinkedInQueryConfig, ScrapeSource } from "@/types";

const props = defineProps<{
  open: boolean;
  busy: boolean;
  linkedinConnected: boolean;
}>();

const emit = defineEmits<{
  close: [];
  submit: [payload: CreateCampaignRequest];
}>();

const { t } = useI18n();

const form = reactive({
  name: "",
  industry: "professional",
  location: "Jakarta",
  max_results: 20,
  source: "google_maps" as ScrapeSource,
  googleQuery: "",
  linkedinKeywords: "",
  linkedinTitle: "",
  linkedinCompany: "",
});

const isLinkedIn = computed(() => form.source === "linkedin");
const canSubmit = computed(() => {
  const hasSharedFields = Boolean(form.name.trim() && form.location.trim()) && !props.busy;
  if (!hasSharedFields) {
    return false;
  }
  if (isLinkedIn.value) {
    return Boolean(form.linkedinKeywords.trim()) && props.linkedinConnected;
  }
  return Boolean(form.googleQuery.trim());
});

function handleSubmit() {
  if (!canSubmit.value) {
    return;
  }

  if (isLinkedIn.value) {
    const queryConfig: LinkedInQueryConfig = {
      keywords: form.linkedinKeywords.trim(),
      title: form.linkedinTitle.trim() || null,
      company: form.linkedinCompany.trim() || null,
      location: form.location.trim(),
    };
    emit("submit", {
      name: form.name.trim(),
      industry: form.industry,
      location: form.location.trim(),
      query: buildLinkedInQuerySummary(queryConfig),
      query_config: queryConfig,
      max_results: form.max_results,
      source: form.source,
    });
    return;
  }

  emit("submit", {
    name: form.name.trim(),
    industry: form.industry,
    location: form.location.trim(),
    query: form.googleQuery.trim(),
    query_config: { query: form.googleQuery.trim() },
    max_results: form.max_results,
    source: form.source,
  });
}
</script>

<template>
  <div v-if="open" class="drawer-backdrop" @click.self="$emit('close')">
    <aside class="drawer-panel panel" aria-label="Campaign creation drawer">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("campaignCreate.kicker") }}</p>
          <h2>{{ t("campaignCreate.title") }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="$emit('close')">
          {{ t("actions.close") }}
        </button>
      </div>

      <p class="drawer-copy">{{ t("campaignCreate.description") }}</p>

      <form class="composer-form" @submit.prevent="handleSubmit">
        <label>
          <span>{{ t("campaignCreate.name") }}</span>
          <input
            v-model="form.name"
            type="text"
            maxlength="120"
            :placeholder="t('campaignCreate.namePlaceholder')"
            required
          />
        </label>

        <div class="composer-grid composer-grid-wide">
          <label>
            <span>{{ t("campaignCreate.source") }}</span>
            <select v-model="form.source">
              <option value="google_maps">{{ t("campaignCreate.sourceOptions.google_maps") }}</option>
              <option value="linkedin">{{ t("campaignCreate.sourceOptions.linkedin") }}</option>
            </select>
          </label>

          <label>
            <span>{{ t("campaignCreate.industry") }}</span>
            <select v-model="form.industry">
              <option value="restaurant">{{ t("campaignCreate.industryOptions.restaurant") }}</option>
              <option value="automotive">{{ t("campaignCreate.industryOptions.automotive") }}</option>
              <option value="retail">{{ t("campaignCreate.industryOptions.retail") }}</option>
              <option value="professional">{{ t("campaignCreate.industryOptions.professional") }}</option>
              <option value="healthcare">{{ t("campaignCreate.industryOptions.healthcare") }}</option>
              <option value="education">{{ t("campaignCreate.industryOptions.education") }}</option>
              <option value="realestate">{{ t("campaignCreate.industryOptions.realestate") }}</option>
            </select>
          </label>

          <label>
            <span>{{ t("campaignCreate.maxResults") }}</span>
            <input v-model.number="form.max_results" type="number" min="1" max="100" />
          </label>
        </div>

        <label>
          <span>{{ t("campaignCreate.location") }}</span>
          <input
            v-model="form.location"
            type="text"
            maxlength="80"
            :placeholder="t('campaignCreate.locationPlaceholder')"
            required
          />
        </label>

        <template v-if="isLinkedIn">
          <label>
            <span>{{ t("campaignCreate.linkedinKeywords") }}</span>
            <input
              v-model="form.linkedinKeywords"
              type="text"
              maxlength="120"
              :placeholder="t('campaignCreate.linkedinKeywordsPlaceholder')"
              required
            />
          </label>

          <div class="composer-grid">
            <label>
              <span>{{ t("campaignCreate.linkedinTitle") }}</span>
              <input
                v-model="form.linkedinTitle"
                type="text"
                maxlength="120"
                :placeholder="t('campaignCreate.linkedinTitlePlaceholder')"
              />
            </label>

            <label>
              <span>{{ t("campaignCreate.linkedinCompany") }}</span>
              <input
                v-model="form.linkedinCompany"
                type="text"
                maxlength="120"
                :placeholder="t('campaignCreate.linkedinCompanyPlaceholder')"
              />
            </label>
          </div>

          <section class="drawer-review" :class="{ 'review-warning': !linkedinConnected }">
            <p class="summary-label">{{ t("campaignCreate.reviewTitle") }}</p>
            <p>
              {{ linkedinConnected ? t("campaignCreate.linkedinReviewDescription") : t("campaignCreate.linkedinDisconnectedDescription") }}
            </p>
          </section>
        </template>

        <template v-else>
          <label>
            <span>{{ t("campaignCreate.query") }}</span>
            <textarea
              v-model="form.googleQuery"
              rows="4"
              maxlength="200"
              :placeholder="t('campaignCreate.queryPlaceholder')"
              required
            />
          </label>

          <section class="drawer-review">
            <p class="summary-label">{{ t("campaignCreate.reviewTitle") }}</p>
            <p>{{ t("campaignCreate.reviewDescription") }}</p>
          </section>
        </template>

        <button class="action-button" :disabled="!canSubmit" type="submit">
          {{ busy ? t("actions.launching") : t("actions.launch") }}
        </button>
      </form>
    </aside>
  </div>
</template>
