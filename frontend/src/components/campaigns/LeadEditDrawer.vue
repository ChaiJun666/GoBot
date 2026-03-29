<script setup lang="ts">
import { reactive, watch } from "vue";
import { useI18n } from "vue-i18n";

import type { EnrichedLead } from "@/types";

const props = defineProps<{
  open: boolean;
  lead: EnrichedLead | null;
}>();

const emit = defineEmits<{
  save: [leadId: string, updates: Record<string, string | null>];
  cancel: [];
}>();

const { t } = useI18n();

const form = reactive({
  name: "",
  address: "",
  location: "",
  phone: "",
  email: "",
  website: "",
  headline: "",
  current_company: "",
  profile_url: "",
  reference_link: "",
  rating: "",
});

watch(
  () => props.lead,
  (lead) => {
    if (!lead) return;
    form.name = lead.name ?? "";
    form.address = lead.address ?? "";
    form.location = lead.location ?? "";
    form.phone = lead.phone ?? "";
    form.email = lead.email ?? "";
    form.website = lead.website ?? "";
    form.headline = lead.headline ?? "";
    form.current_company = lead.current_company ?? "";
    form.profile_url = lead.profile_url ?? "";
    form.reference_link = lead.reference_link ?? "";
    form.rating = lead.rating ?? "";
  },
  { immediate: true },
);

function handleSubmit() {
  if (!props.lead) return;
  const updates: Record<string, string | null> = {};
  const fields: (keyof typeof form)[] = [
    "name", "address", "location", "phone", "email", "website",
    "headline", "current_company", "profile_url", "reference_link", "rating",
  ];
  for (const key of fields) {
    const value = form[key].trim() || null;
    if (value !== (props.lead![key] ?? null)) {
      updates[key] = value;
    }
  }
  emit("save", props.lead.id, updates);
}
</script>

<template>
  <div v-if="open && lead" class="drawer-backdrop" @click.self="emit('cancel')">
    <aside class="drawer-panel panel" aria-label="Edit lead drawer">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("leadTable.editTitle") }}</p>
          <h2>{{ lead.name }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="emit('cancel')">
          {{ t("actions.close") }}
        </button>
      </div>

      <form class="composer-form" @submit.prevent="handleSubmit">
        <label>
          <span>{{ t("leadTable.details.headline") }}</span>
          <input v-model="form.name" type="text" maxlength="120" required />
        </label>
        <label>
          <span>{{ t("leadTable.details.address") }}</span>
          <input v-model="form.address" type="text" maxlength="200" />
        </label>
        <div class="composer-grid">
          <label>
            <span>{{ t("leadTable.details.location") }}</span>
            <input v-model="form.location" type="text" maxlength="80" />
          </label>
          <label>
            <span>{{ t("leadTable.details.phone") }}</span>
            <input v-model="form.phone" type="text" maxlength="40" />
          </label>
        </div>
        <div class="composer-grid">
          <label>
            <span>{{ t("leadTable.details.email") }}</span>
            <input v-model="form.email" type="text" maxlength="120" />
          </label>
          <label>
            <span>{{ t("leadTable.details.website") }}</span>
            <input v-model="form.website" type="text" maxlength="200" />
          </label>
        </div>
        <div class="composer-grid">
          <label>
            <span>{{ t("leadTable.details.company") }}</span>
            <input v-model="form.current_company" type="text" maxlength="120" />
          </label>
          <label>
            <span>{{ t("leadTable.details.rating") }}</span>
            <input v-model="form.rating" type="text" maxlength="10" />
          </label>
        </div>
        <label>
          <span>{{ t("leadTable.details.profileUrl") }}</span>
          <input v-model="form.profile_url" type="text" maxlength="300" />
        </label>
        <label>
          <span>{{ t("leadTable.details.sourceLink") }}</span>
          <input v-model="form.reference_link" type="text" maxlength="300" />
        </label>
        <div class="panel-actions">
          <button class="action-button" type="submit">{{ t("leadTable.saveLead") }}</button>
          <button class="ghost-button" type="button" @click="emit('cancel')">{{ t("leadTable.cancelEdit") }}</button>
        </div>
      </form>
    </aside>
  </div>
</template>
