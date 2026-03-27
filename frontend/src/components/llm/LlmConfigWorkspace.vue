<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import type {
  CreateLlmConfigRequest,
  LlmConfigSummary,
  LlmProviderKey,
  LlmProviderPreset,
  UpdateLlmConfigRequest,
} from "@/types";

const props = defineProps<{
  configs: LlmConfigSummary[];
  providers: LlmProviderPreset[];
  selectedConfigId: string | null;
  loadingConfigs: boolean;
  busy: boolean;
}>();

const emit = defineEmits<{
  createConfig: [payload: CreateLlmConfigRequest];
  updateConfig: [configId: string, payload: UpdateLlmConfigRequest];
  deleteConfig: [configId: string];
  activateConfig: [configId: string];
  deactivateConfig: [configId: string];
  selectConfig: [configId: string];
}>();

const { t } = useI18n();

const showForm = ref(false);
const form = reactive({
  provider: "openai" as LlmProviderKey,
  display_name: "",
  model_name: "",
  base_url: "",
  api_key: "",
  note: "",
  official_url: "",
});

const editingId = ref<string | null>(null);
const showApiKey = ref(false);
const deletingId = ref<string | null>(null);

const selectedConfig = computed(
  () => props.configs.find((c) => c.id === props.selectedConfigId) ?? null,
);

const isEditing = computed(() => editingId.value !== null);
const formTitle = computed(() =>
  isEditing.value ? t("llm.editConfigTitle") : t("llm.createConfigTitle"),
);
const submitLabel = computed(() =>
  props.busy ? t("llm.saving") : isEditing.value ? t("llm.saveConfig") : t("llm.addConfig"),
);
const canSubmit = computed(() => {
  if (!form.display_name.trim() || !form.model_name.trim() || !form.base_url.trim()) {
    return false;
  }
  if (!isEditing.value && !form.api_key.trim()) {
    return false;
  }
  return true;
});

const providerPreset = computed(
  () => props.providers.find((p) => p.key === form.provider) ?? null,
);

watch(
  () => form.provider,
  (key) => {
    const preset = props.providers.find((p) => p.key === key);
    if (preset) {
      form.base_url = preset.default_base_url;
      form.official_url = preset.official_url;
    }
  },
);

function resetForm() {
  editingId.value = null;
  showApiKey.value = false;
  form.provider = "openai";
  form.display_name = "";
  form.model_name = "";
  form.base_url = providerPreset.value?.default_base_url ?? "";
  form.api_key = "";
  form.note = "";
  form.official_url = providerPreset.value?.official_url ?? "";
}

function startCreate() {
  resetForm();
  showForm.value = true;
}

function startEdit(config: LlmConfigSummary) {
  editingId.value = config.id;
  showApiKey.value = false;
  form.provider = config.provider as LlmProviderKey;
  form.display_name = config.display_name;
  form.model_name = config.model_name;
  form.base_url = config.base_url;
  form.api_key = "";
  form.note = config.note ?? "";
  form.official_url = config.official_url ?? "";
  showForm.value = true;
}

function cancelForm() {
  showForm.value = false;
  resetForm();
}

function submit() {
  if (isEditing.value && editingId.value) {
    emit("updateConfig", editingId.value, {
      display_name: form.display_name.trim() || null,
      model_name: form.model_name.trim() || null,
      base_url: form.base_url.trim() || null,
      api_key: form.api_key.trim() || null,
      note: form.note.trim() || null,
      official_url: form.official_url.trim() || null,
    });
    return;
  }
  emit("createConfig", {
    provider: form.provider,
    display_name: form.display_name.trim(),
    model_name: form.model_name.trim(),
    base_url: form.base_url.trim(),
    api_key: form.api_key.trim(),
    note: form.note.trim() || null,
    official_url: form.official_url.trim() || null,
  });
}

function confirmDelete(configId: string) {
  deletingId.value = configId;
}

function cancelDelete() {
  deletingId.value = null;
}

function doDelete() {
  if (deletingId.value) {
    emit("deleteConfig", deletingId.value);
    deletingId.value = null;
  }
}

function formatDate(value: string | null): string {
  if (!value) return t("common.never");
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

defineExpose({ startCreate, startEdit, cancelForm });
</script>

<template>
  <section class="mail-workspace">
    <!-- Left sidebar: config list -->
    <section class="panel mail-sidebar">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("llm.configsKicker") }}</p>
          <h2>{{ t("llm.configsTitle") }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="startCreate">
          {{ t("llm.addConfig") }}
        </button>
      </div>

      <div v-if="configs.length" class="mailbox-list">
        <button
          v-for="config in configs"
          :key="config.id"
          class="mailbox-card"
          :class="{ selected: config.id === selectedConfigId }"
          type="button"
          @click="$emit('selectConfig', config.id)"
        >
          <div class="mailbox-card-top">
            <strong>{{ config.display_name }}</strong>
            <span
              v-if="config.is_active"
              class="status-badge"
              data-status="completed"
            >
              {{ t("common.enabled") }}
            </span>
          </div>
          <p class="job-meta">{{ config.provider }} / {{ config.model_name }}</p>
          <p v-if="config.note" class="job-meta">{{ config.note }}</p>
          <p class="job-meta">{{ t("llm.updatedLabel") }}: {{ formatDate(config.updated_at) }}</p>
        </button>
      </div>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("llm.noConfigsTitle") }}</p>
        <span>{{ t("llm.noConfigsDescription") }}</span>
      </div>

      <!-- Create / Edit form (hidden by default) -->
      <form v-if="showForm" class="composer-form" @submit.prevent="submit">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("llm.configFormKicker") }}</p>
          <h2>{{ formTitle }}</h2>
        </div>

        <label>
          <span>{{ t("llm.provider") }}</span>
          <select v-model="form.provider" :disabled="isEditing">
            <option v-for="preset in providers" :key="preset.key" :value="preset.key">
              {{ preset.display_name }}
            </option>
          </select>
        </label>

        <label>
          <span>{{ t("llm.displayName") }}</span>
          <input v-model="form.display_name" type="text" maxlength="120" />
        </label>

        <label>
          <span>{{ t("llm.modelName") }}</span>
          <input v-model="form.model_name" type="text" maxlength="120" />
        </label>

        <label>
          <span>{{ t("llm.baseUrl") }}</span>
          <input v-model="form.base_url" type="url" />
        </label>

        <label>
          <span>{{ t("llm.apiKey") }}</span>
          <div class="api-key-input">
            <input
              v-model="form.api_key"
              :type="showApiKey ? 'text' : 'password'"
              autocomplete="off"
              :placeholder="isEditing ? t('llm.apiKeyPlaceholder') : ''"
            />
            <button
              type="button"
              class="ghost-button"
              @click="showApiKey = !showApiKey"
            >
              {{ showApiKey ? t("llm.hideApiKey") : t("llm.showApiKey") }}
            </button>
          </div>
        </label>

        <label>
          <span>{{ t("llm.officialUrl") }} <span class="optional-hint">({{ t("common.none") }})</span></span>
          <input v-model="form.official_url" type="url" />
        </label>

        <label>
          <span>{{ t("llm.note") }} <span class="optional-hint">({{ t("common.none") }})</span></span>
          <input v-model="form.note" type="text" maxlength="300" />
        </label>

        <div class="panel-actions">
          <button class="action-button" type="submit" :disabled="!canSubmit || busy">
            {{ submitLabel }}
          </button>
          <button
            class="ghost-button"
            type="button"
            @click="cancelForm"
          >
            {{ t("actions.cancel") }}
          </button>
        </div>
      </form>
    </section>

    <!-- Right panel: config detail -->
    <section class="panel mail-list-panel">
      <template v-if="selectedConfig">
        <div class="panel-toolbar">
          <div class="panel-heading">
            <p class="panel-kicker">{{ t("llm.detailKicker") }}</p>
            <h2>{{ selectedConfig.display_name }}</h2>
          </div>
          <div class="panel-actions">
            <button
              v-if="!selectedConfig.is_active"
              class="action-button"
              type="button"
              @click="$emit('activateConfig', selectedConfig.id)"
            >
              {{ t("llm.activate") }}
            </button>
            <button
              v-else
              class="ghost-button"
              type="button"
              @click="$emit('deactivateConfig', selectedConfig.id)"
            >
              {{ t("llm.deactivate") }}
            </button>
            <button
              class="ghost-button"
              type="button"
              @click="startEdit(selectedConfig)"
            >
              {{ t("llm.editConfig") }}
            </button>
            <button
              class="ghost-button danger-ghost"
              type="button"
              @click="confirmDelete(selectedConfig.id)"
            >
              {{ t("llm.deleteConfig") }}
            </button>
          </div>
        </div>

        <dl class="detail-grid">
          <div>
            <dt>{{ t("llm.provider") }}</dt>
            <dd>{{ selectedConfig.provider }}</dd>
          </div>
          <div>
            <dt>{{ t("llm.modelName") }}</dt>
            <dd>{{ selectedConfig.model_name }}</dd>
          </div>
          <div>
            <dt>{{ t("llm.baseUrl") }}</dt>
            <dd>{{ selectedConfig.base_url }}</dd>
          </div>
          <div v-if="selectedConfig.official_url">
            <dt>{{ t("llm.officialUrl") }}</dt>
            <dd>{{ selectedConfig.official_url }}</dd>
          </div>
          <div>
            <dt>{{ t("llm.apiKeyStatus") }}</dt>
            <dd>{{ selectedConfig.has_api_key ? t("common.enabled") : t("common.unavailable") }}</dd>
          </div>
          <div v-if="selectedConfig.note">
            <dt>{{ t("llm.note") }}</dt>
            <dd>{{ selectedConfig.note }}</dd>
          </div>
          <div>
            <dt>{{ t("llm.status") }}</dt>
            <dd>{{ selectedConfig.is_active ? t("common.enabled") : t("common.disabled") }}</dd>
          </div>
          <div>
            <dt>{{ t("llm.updatedLabel") }}</dt>
            <dd>{{ formatDate(selectedConfig.updated_at) }}</dd>
          </div>
        </dl>

        <!-- Delete confirmation -->
        <div v-if="deletingId === selectedConfig.id" class="delete-confirm">
          <InlineStatusNotice
            :title="t('llm.deleteConfirmTitle')"
            :detail="t('llm.deleteConfirmDescription', { name: selectedConfig.display_name })"
            tone="warning"
          />
          <div class="panel-actions" style="margin-top: 0.5rem">
            <button class="action-button" type="button" @click="doDelete">
              {{ t("llm.confirmDelete") }}
            </button>
            <button class="ghost-button" type="button" @click="cancelDelete">
              {{ t("actions.close") }}
            </button>
          </div>
        </div>
      </template>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("llm.selectConfigTitle") }}</p>
        <span>{{ t("llm.selectConfigDescription") }}</span>
      </div>
    </section>
  </section>
</template>

<style scoped>
.api-key-input {
  display: flex;
  gap: 0.25rem;
}
.api-key-input input {
  flex: 1;
}
.api-key-input .ghost-button {
  flex-shrink: 0;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}
.optional-hint {
  opacity: 0.5;
  font-weight: 400;
}
.delete-confirm {
  margin-top: 1rem;
}
.danger-ghost {
  color: var(--color-danger);
}
.danger-ghost:hover {
  background: var(--color-danger);
  color: white;
}
</style>
