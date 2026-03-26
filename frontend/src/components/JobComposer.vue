<script setup lang="ts">
import { reactive } from "vue";
import { useI18n } from "vue-i18n";

import type { CreateScrapeJobRequest } from "@/types";

const props = defineProps<{
  busy: boolean;
}>();

const emit = defineEmits<{
  submit: [payload: CreateScrapeJobRequest];
}>();

const { t } = useI18n();

const form = reactive<CreateScrapeJobRequest>({
  query: "",
  max_results: 20,
  source: "google_maps",
});

function handleSubmit() {
  emit("submit", {
    query: form.query.trim(),
    max_results: form.max_results,
    source: form.source,
  });
}
</script>

<template>
  <section class="panel panel-form">
    <div class="panel-heading">
      <p class="panel-kicker">{{ t("legacy.jobComposer.kicker") }}</p>
      <h2>{{ t("legacy.jobComposer.title") }}</h2>
    </div>
    <form class="composer-form" @submit.prevent="handleSubmit">
      <label>
        <span>{{ t("legacy.jobComposer.query") }}</span>
        <textarea
          v-model="form.query"
          rows="4"
          maxlength="200"
          :placeholder="t('campaignCreate.queryPlaceholder')"
          required
        />
      </label>

      <div class="composer-grid">
        <label>
          <span>{{ t("legacy.jobComposer.source") }}</span>
          <select v-model="form.source">
            <option value="google_maps">Google Maps</option>
          </select>
        </label>

        <label>
          <span>{{ t("campaignCreate.maxResults") }}</span>
          <input v-model.number="form.max_results" type="number" min="1" max="100" />
        </label>
      </div>

      <button class="action-button" :disabled="busy || !form.query.trim()" type="submit">
        {{ busy ? t("actions.launching") : t("legacy.jobComposer.title") }}
      </button>
    </form>
  </section>
</template>
