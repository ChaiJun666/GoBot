<script setup lang="ts">
import { computed, reactive, ref } from "vue";
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
const showPassword = ref(false);

const canSubmit = computed(
  () => Boolean(form.username.trim() && form.password.trim()) && !props.busy,
);
const passwordInputType = computed(() => (showPassword.value ? "text" : "password"));
const passwordToggleLabel = computed(() =>
  showPassword.value ? t("linkedin.hidePassword") : t("linkedin.showPassword"),
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
  showPassword.value = false;
}

function togglePasswordVisibility() {
  showPassword.value = !showPassword.value;
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

    <form v-if="!session?.connected" class="composer-form" @submit.prevent="handleSubmit">
      <label>
        <span>{{ t("linkedin.username") }}</span>
        <input v-model="form.username" type="text" autocomplete="username" />
      </label>

      <label>
        <span>{{ t("linkedin.password") }}</span>
        <div class="password-field">
          <input
            v-model="form.password"
            :type="passwordInputType"
            autocomplete="current-password"
          />
          <button
            class="password-toggle"
            type="button"
            :aria-label="passwordToggleLabel"
            :title="passwordToggleLabel"
            @click="togglePasswordVisibility"
          >
            <svg
              v-if="showPassword"
              viewBox="0 0 24 24"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M3 4.5 19.5 21"
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.8"
              />
              <path
                d="M10.7 6.2A10.9 10.9 0 0 1 12 6c5.4 0 9.2 4.3 10 6-.4.8-1.5 2.5-3.3 4"
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.8"
              />
              <path
                d="M14.1 14.1A3 3 0 0 1 9.9 9.9"
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.8"
              />
              <path
                d="M6.2 7.4C3.7 9 2.3 11.3 2 12c.8 1.7 4.6 6 10 6 1.3 0 2.5-.2 3.5-.6"
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.8"
              />
            </svg>
            <svg
              v-else
              viewBox="0 0 24 24"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M2 12c.8-1.7 4.6-6 10-6s9.2 4.3 10 6c-.8 1.7-4.6 6-10 6S2.8 13.7 2 12Z"
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.8"
              />
              <circle
                cx="12"
                cy="12"
                r="3"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
              />
            </svg>
          </button>
        </div>
      </label>

      <div class="panel-actions">
        <button class="action-button" type="submit" :disabled="!canSubmit">
          {{ busy ? t("linkedin.connecting") : t("linkedin.connect") }}
        </button>
      </div>
    </form>

    <div v-else class="panel-actions">
      <button
        class="ghost-button"
        type="button"
        :disabled="busy"
        @click="$emit('disconnect')"
      >
        {{ t("linkedin.disconnect") }}
      </button>
    </div>
  </section>
</template>
