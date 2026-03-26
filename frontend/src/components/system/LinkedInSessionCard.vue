<script setup lang="ts">
import { computed, reactive } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
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

const sessionStateLabel = computed(() =>
  props.session?.connected ? t("linkedin.connected") : t("linkedin.disconnected"),
);

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return t("common.never");
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

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
  <section class="panel panel-detail session-panel">
    <div class="session-hero">
      <div class="panel-heading session-copy">
        <p class="panel-kicker">{{ t("linkedin.sessionKicker") }}</p>
        <h2>{{ t("linkedin.sessionTitle") }}</h2>
        <p class="drawer-copy">{{ t("linkedin.sessionDescription") }}</p>
      </div>
      <div class="session-state-card" :data-connected="session?.connected ? 'true' : 'false'">
        <span class="summary-label">{{ t("linkedin.sessionState") }}</span>
        <strong :class="['session-state', session?.connected ? 'is-online' : 'is-offline']">
          {{ sessionStateLabel }}
        </strong>
      </div>
    </div>

    <div class="session-grid">
      <div class="drawer-review">
        <p class="summary-label">{{ t("linkedin.connectedAs") }}</p>
        <p>{{ session?.account_label ?? t("common.none") }}</p>
      </div>
      <div class="drawer-review">
        <p class="summary-label">{{ t("linkedin.updatedAt") }}</p>
        <p>{{ formatDate(session?.updated_at) }}</p>
      </div>
    </div>

    <InlineStatusNotice
      v-if="session?.last_error"
      :title="t('notices.failureTitle')"
      :detail="session.last_error"
      tone="warning"
    />

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
