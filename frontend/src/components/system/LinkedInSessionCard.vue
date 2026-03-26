<script setup lang="ts">
import { computed, reactive } from "vue";
import { useI18n } from "vue-i18n";

import type { ConnectLinkedInSessionRequest, LinkedInSessionStatus } from "@/types";

const props = defineProps<{
  session: LinkedInSessionStatus | null;
  busy: boolean;
}>();

const emit = defineEmits<{
  connect: [payload: ConnectLinkedInSessionRequest];
  disconnect: [];
}>();

const { t } = useI18n();
const form = reactive({
  username: "",
  password: "",
});

const canSubmit = computed(
  () => Boolean(form.username.trim() && form.password.trim()) && !props.busy,
);

function handleSubmit() {
  if (!canSubmit.value) {
    return;
  }
  emit("connect", {
    username: form.username.trim(),
    password: form.password,
  });
  form.password = "";
}
</script>

<template>
  <section class="panel panel-detail">
    <div class="panel-toolbar">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("linkedin.sessionKicker") }}</p>
        <h2>{{ t("linkedin.sessionTitle") }}</h2>
      </div>
      <strong :class="['session-state', session?.connected ? 'is-online' : 'is-offline']">
        {{ session?.connected ? t("linkedin.connected") : t("linkedin.disconnected") }}
      </strong>
    </div>

    <p class="drawer-copy">{{ t("linkedin.sessionDescription") }}</p>

    <div v-if="session?.connected" class="drawer-review">
      <p class="summary-label">{{ t("linkedin.connectedAs") }}</p>
      <p>{{ session.account_label ?? t("common.unknown") }}</p>
    </div>

    <p v-if="session?.last_error" class="job-error">{{ session.last_error }}</p>

    <form class="composer-form" @submit.prevent="handleSubmit">
      <label>
        <span>{{ t("linkedin.username") }}</span>
        <input v-model="form.username" type="text" autocomplete="username" />
      </label>

      <label>
        <span>{{ t("linkedin.password") }}</span>
        <input v-model="form.password" type="password" autocomplete="current-password" />
      </label>

      <div class="panel-actions">
        <button class="action-button" type="submit" :disabled="!canSubmit">
          {{ busy ? t("linkedin.connecting") : t("linkedin.connect") }}
        </button>
        <button
          v-if="session?.connected"
          class="ghost-button"
          type="button"
          :disabled="busy"
          @click="$emit('disconnect')"
        >
          {{ t("linkedin.disconnect") }}
        </button>
      </div>
    </form>
  </section>
</template>
