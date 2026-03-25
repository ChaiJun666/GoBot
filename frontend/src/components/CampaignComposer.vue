<script setup lang="ts">
import { reactive } from "vue";

import type { CreateCampaignRequest } from "@/types";

defineProps<{
  busy: boolean;
}>();

const emit = defineEmits<{
  submit: [payload: CreateCampaignRequest];
}>();

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
      <p class="panel-kicker">Campaigns</p>
      <h2>Launch an intelligence run</h2>
    </div>
    <form class="composer-form" @submit.prevent="handleSubmit">
      <label>
        <span>Campaign name</span>
        <input v-model="form.name" type="text" maxlength="120" placeholder="Jakarta coffee market" required />
      </label>

      <div class="composer-grid composer-grid-wide">
        <label>
          <span>Industry</span>
          <select v-model="form.industry">
            <option value="restaurant">Restaurant</option>
            <option value="automotive">Automotive</option>
            <option value="retail">Retail</option>
            <option value="professional">Professional</option>
            <option value="healthcare">Healthcare</option>
            <option value="education">Education</option>
            <option value="realestate">Real estate</option>
          </select>
        </label>

        <label>
          <span>Location</span>
          <input v-model="form.location" type="text" maxlength="80" placeholder="Jakarta" required />
        </label>

        <label>
          <span>Max results</span>
          <input v-model.number="form.max_results" type="number" min="1" max="100" />
        </label>
      </div>

      <label>
        <span>Search query</span>
        <textarea
          v-model="form.query"
          rows="4"
          maxlength="200"
          placeholder="Coffee shops Jakarta Selatan"
          required
        />
      </label>

      <button class="action-button" :disabled="busy || !form.name.trim() || !form.query.trim()" type="submit">
        {{ busy ? "Launching..." : "Launch campaign" }}
      </button>
    </form>
  </section>
</template>
