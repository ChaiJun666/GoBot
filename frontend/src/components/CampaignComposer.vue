<script setup lang="ts">
import { reactive } from "vue";
import { useI18n } from "vue-i18n";

import type { CreateCampaignRequest } from "@/types";

defineProps<{
  busy: boolean;
}>();

const emit = defineEmits<{
  submit: [payload: CreateCampaignRequest];
}>();

const { t } = useI18n();

const form = reactive<CreateCampaignRequest>({
  name: "",
  industry: "professional",
  location: "Jakarta",
  query: "",
  max_results: 20,
  source: "google_maps",
});

function handleSubmit() {
  emit("submit", {
    name: form.name.trim(),
    industry: form.industry,
    location: form.location.trim(),
    query: form.query.trim(),
    max_results: form.max_results,
    source: form.source,
  });
}
</script>

<template>
  <section class="panel panel-form">
    <div class="panel-heading">
      <p class="panel-kicker">{{ t("legacy.campaignComposer.kicker") }}</p>
      <h2>{{ t("campaignCreate.title") }}</h2>
    </div>
    <form class="composer-form" @submit.prevent="handleSubmit">
      <label>
        <span>{{ t("campaignCreate.name") }}</span>
        <input v-model="form.name" type="text" maxlength="120" :placeholder="t('campaignCreate.namePlaceholder')" required />
      </label>

      <div class="composer-grid composer-grid-wide">
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
          <span>{{ t("campaignCreate.location") }}</span>
          <input v-model="form.location" type="text" maxlength="80" :placeholder="t('campaignCreate.locationPlaceholder')" required />
        </label>

        <label>
          <span>{{ t("campaignCreate.maxResults") }}</span>
          <input v-model.number="form.max_results" type="number" min="1" max="100" />
        </label>
      </div>

      <label>
        <span>{{ t("campaignCreate.query") }}</span>
        <textarea
          v-model="form.query"
          rows="4"
          maxlength="200"
          :placeholder="t('campaignCreate.queryPlaceholder')"
          required
        />
      </label>

      <button class="action-button" :disabled="busy || !form.name.trim() || !form.query.trim()" type="submit">
        {{ busy ? t("actions.launching") : t("actions.launch") }}
      </button>
    </form>
  </section>
</template>
