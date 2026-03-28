<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import type {
  GeneratedEmail,
  GenerateEmailsRequest,
  LeadOutreachSummary,
  MailboxSummary,
  OutreachLanguage,
  OutreachSendEmailItem,
  SendOutreachEmailsResponse,
} from "@/types";
import { api } from "@/lib/api";

const STAGE_LABELS = ["", "stage1", "stage2", "stage3", "stage4", "stage5"] as const;

const props = defineProps<{
  leads: LeadOutreachSummary[];
  mailboxes: MailboxSummary[];
  loadingLeads: boolean;
  busy: boolean;
  hasActiveLlm: boolean;
}>();

const emit = defineEmits<{
  refreshLeads: [];
  message: [text: string, tone: "info" | "success" | "warning" | "danger"];
}>();

const { t } = useI18n();

const selectedLeadIds = ref<Set<string>>(new Set());
const stageFilter = ref<number | null>(null);
const selectedMailboxId = ref<string | null>(null);
const languageOverride = ref<OutreachLanguage | "auto">("auto");
const userInstructions = ref("");
const generatedEmails = ref<Map<string, GeneratedEmail>>(new Map());
const editingEmails = reactive<Map<string, { subject: string; body: string }>>(new Map());
const generating = ref(false);
const sending = ref(false);
const sendResults = ref<SendOutreachEmailsResponse | null>(null);
const previewLeadId = ref<string | null>(null);

const filteredLeads = computed(() => {
  if (stageFilter.value == null) return props.leads;
  return props.leads.filter((l) => l.current_stage === stageFilter.value);
});

const previewLead = computed(() =>
  props.leads.find((l) => l.lead_id === previewLeadId.value) ?? null,
);

const previewEmail = computed(() => {
  if (!previewLeadId.value) return null;
  const editing = editingEmails.get(previewLeadId.value);
  if (editing) return editing;
  const generated = generatedEmails.value.get(previewLeadId.value);
  if (generated) return { subject: generated.subject, body: generated.body };
  return null;
});

const canGenerate = computed(() =>
  selectedLeadIds.value.size > 0 && props.hasActiveLlm && !generating.value,
);

const canSend = computed(() =>
  selectedMailboxId.value &&
  selectedLeadIds.value.size > 0 &&
  Array.from(selectedLeadIds.value).every((id) => editingEmails.has(id) || generatedEmails.value.has(id)) &&
  !sending.value,
);

function toggleLead(leadId: string) {
  const next = new Set(selectedLeadIds.value);
  if (next.has(leadId)) next.delete(leadId);
  else next.add(leadId);
  selectedLeadIds.value = next;
  if (next.size === 1 && !previewLeadId.value) previewLeadId.value = leadId;
}

function selectLeadForPreview(leadId: string) {
  previewLeadId.value = leadId;
}

function stageLabel(stage: number): string {
  return t(`outreach.${STAGE_LABELS[stage]}`) || `Stage ${stage}`;
}

async function generateEmails() {
  generating.value = true;
  sendResults.value = null;
  try {
    const payload: GenerateEmailsRequest = {
      lead_ids: Array.from(selectedLeadIds.value),
      language: languageOverride.value === "auto" ? null : languageOverride.value,
      user_instructions: userInstructions.value.trim() || null,
    };
    const resp = await api.generateEmails(payload);
    const map = new Map<string, GeneratedEmail>();
    for (const email of resp.emails) {
      map.set(email.lead_id, email);
    }
    generatedEmails.value = map;
    editingEmails.clear();
    if (resp.errors.length) {
      emit("message", t("outreach.errorCount", { count: resp.errors.length }), "warning");
    } else {
      emit("message", t("outreach.generatedCount", { count: resp.emails.length }), "success");
    }
  } catch (error) {
    emit("message", error instanceof Error ? error.message : "Generation failed", "danger");
  } finally {
    generating.value = false;
  }
}

async function sendEmails() {
  if (!selectedMailboxId.value) return;
  sending.value = true;
  try {
    const emails: OutreachSendEmailItem[] = [];
    for (const leadId of selectedLeadIds.value) {
      const editing = editingEmails.get(leadId);
      const generated = generatedEmails.value.get(leadId);
      const email = editing ?? (generated ? { subject: generated.subject, body: generated.body } : null);
      if (!email) continue;
      emails.push({
        lead_id: leadId,
        mailbox_id: selectedMailboxId.value,
        subject: email.subject,
        body: email.body,
      });
    }
    const resp = await api.sendOutreachEmails({ emails });
    sendResults.value = resp;
    const sentCount = resp.results.filter((r) => r.status === "sent").length;
    emit("message", t("outreach.sentCount", { count: sentCount }), "success");
    editingEmails.clear();
    generatedEmails.value = new Map();
    selectedLeadIds.value = new Set();
    previewLeadId.value = null;
    emit("refreshLeads");
  } catch (error) {
    emit("message", error instanceof Error ? error.message : "Send failed", "danger");
  } finally {
    sending.value = false;
  }
}

function updateEditing(field: "subject" | "body", value: string) {
  if (!previewLeadId.value) return;
  const current = editingEmails.get(previewLeadId.value) ??
    (() => {
      const g = generatedEmails.value.get(previewLeadId.value);
      return g ? { subject: g.subject, body: g.body } : { subject: "", body: "" };
    })();
  editingEmails.set(previewLeadId.value, { ...current, [field]: value });
}

watch(
  () => props.mailboxes,
  (mailboxes) => {
    if (!selectedMailboxId.value || !mailboxes.some((m) => m.id === selectedMailboxId.value)) {
      selectedMailboxId.value = mailboxes.length ? mailboxes[0].id : null;
    }
  },
  { immediate: true },
);
</script>

<template>
  <section class="mail-workspace">
    <!-- Left: lead list -->
    <section class="panel mail-sidebar">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("outreach.listKicker") }}</p>
          <h2>{{ t("outreach.listTitle") }}</h2>
        </div>
        <div class="panel-actions" style="gap:0.25rem">
          <select v-model="stageFilter" class="ghost-button" style="font-size:0.75rem;padding:0.2rem 0.5rem">
            <option :value="null">{{ t("outreach.stage") }}: All</option>
            <option v-for="s in [1,2,3,4,5]" :key="s" :value="s">{{ stageLabel(s) }}</option>
          </select>
          <button class="ghost-button" type="button" @click="$emit('refreshLeads')">{{ t("actions.refresh") }}</button>
        </div>
      </div>

      <div v-if="loadingLeads" class="empty-state compact-empty">
        <p>Loading...</p>
      </div>
      <div v-else-if="filteredLeads.length" class="mailbox-list">
        <button v-for="lead in filteredLeads" :key="lead.lead_id"
          class="mailbox-card" :class="{ selected: selectedLeadIds.has(lead.lead_id) }"
          type="button" @click="toggleLead(lead.lead_id); selectLeadForPreview(lead.lead_id)">
          <div class="mailbox-card-top">
            <label class="checkbox-label" @click.stop>
              <input type="checkbox" :checked="selectedLeadIds.has(lead.lead_id)"
                @change="toggleLead(lead.lead_id)" />
              <strong>{{ lead.lead_name }}</strong>
            </label>
            <span class="status-badge" :data-status="lead.current_stage <= 2 ? 'completed' : lead.current_stage >= 4 ? 'running' : 'queued'">
              {{ stageLabel(lead.current_stage) }}
            </span>
          </div>
          <p class="job-meta">{{ lead.lead_company || lead.lead_email }}</p>
          <p class="job-meta">{{ t("outreach.emailsSent") }}: {{ lead.emails_sent }}</p>
        </button>
      </div>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("outreach.noLeadsTitle") }}</p>
        <span>{{ t("outreach.noLeadsDescription") }}</span>
      </div>
    </section>

    <!-- Center: email preview -->
    <section class="panel mail-list-panel">
      <template v-if="previewLead">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("outreach.previewKicker") }}</p>
          <h2>{{ t("outreach.previewTitle") }}</h2>
        </div>
        <div class="detail-grid">
          <div><dt>{{ t("outreach.company") }}</dt><dd>{{ previewLead.lead_company || "—" }}</dd></div>
          <div><dt>{{ t("outreach.stage") }}</dt><dd>{{ stageLabel(previewLead.current_stage) }}</dd></div>
          <div><dt>{{ t("outreach.campaign") }}</dt><dd>{{ previewLead.campaign_name || "—" }}</dd></div>
        </div>
        <div v-if="previewEmail" class="email-preview-form">
          <label>
            <span>{{ t("mail.subject") }}</span>
            <input :value="previewEmail.subject" type="text"
              @input="updateEditing('subject', ($event.target as HTMLInputElement).value)" />
          </label>
          <label>
            <span>{{ t("mail.body") }}</span>
            <textarea :value="previewEmail.body" rows="12"
              @input="updateEditing('body', ($event.target as HTMLTextAreaElement).value)" />
          </label>
        </div>
        <div v-else class="empty-state compact-empty">
          <p>{{ t("outreach.noPreviewTitle") }}</p>
          <span>{{ t("outreach.noPreviewDescription") }}</span>
        </div>
      </template>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("outreach.selectLeadTitle") }}</p>
        <span>{{ t("outreach.selectLeadDescription") }}</span>
      </div>
    </section>

    <!-- Right: controls -->
    <section class="panel mail-sidebar" style="max-width:280px">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("outreach.controlKicker") }}</p>
        <h2>{{ t("outreach.controlTitle") }}</h2>
      </div>

      <InlineStatusNotice v-if="!hasActiveLlm"
        :title="t('outreach.noLlm')" tone="warning" />
      <InlineStatusNotice v-if="!mailboxes.length"
        :title="t('outreach.noMailbox')" tone="warning" />

      <div class="control-stack">
        <label>
          <span>{{ t("outreach.fromMailbox") }}</span>
          <select v-model="selectedMailboxId" :disabled="!mailboxes.length">
            <option :value="null" disabled>{{ t("outreach.selectMailbox") }}</option>
            <option v-for="m in mailboxes" :key="m.id" :value="m.id">{{ m.email_address }}</option>
          </select>
        </label>

        <label>
          <span>{{ t("outreach.language") }}</span>
          <select v-model="languageOverride">
            <option value="auto">{{ t("outreach.languageAuto") }}</option>
            <option value="en">{{ t("outreach.languageEn") }}</option>
            <option value="zh">{{ t("outreach.languageZh") }}</option>
          </select>
        </label>

        <label>
          <span>{{ t("outreach.userInstructions") }}</span>
          <textarea v-model="userInstructions" rows="3"
            :placeholder="t('outreach.userInstructionsPlaceholder')" />
        </label>

        <p class="job-meta">{{ t("outreach.selectLeadsHint") }}</p>

        <div class="panel-actions" style="flex-direction:column">
          <button class="action-button" type="button"
            :disabled="!canGenerate" @click="generateEmails">
            {{ generating ? t("outreach.generating") : t("outreach.generateBtn") }}
          </button>
          <button class="action-button" type="button"
            :disabled="!canSend" @click="sendEmails">
            {{ sending ? t("outreach.sending") : t("outreach.sendBtn") }}
          </button>
        </div>

        <div v-if="sendResults" class="send-results">
          <p class="panel-kicker">{{ t("outreach.resultsTitle") }}</p>
          <div v-for="r in sendResults.results" :key="r.lead_id" class="job-meta" :style="{ color: r.status === 'sent' ? 'var(--color-success)' : 'var(--color-danger)' }">
            {{ r.lead_id.slice(0, 8) }}: {{ r.status }}{{ r.error ? ` — ${r.error}` : "" }}
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.control-stack { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }
.control-stack label { display: flex; flex-direction: column; gap: 0.15rem; font-size: 0.8rem; }
.control-stack select, .control-stack textarea, .control-stack input {
  font-size: 0.8rem; padding: 0.3rem 0.5rem; border: 1px solid var(--color-border); border-radius: 4px;
  background: var(--color-surface); color: var(--color-text);
}
.email-preview-form { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }
.email-preview-form label { display: flex; flex-direction: column; gap: 0.15rem; font-size: 0.8rem; }
.email-preview-form input, .email-preview-form textarea {
  font-size: 0.8rem; padding: 0.3rem 0.5rem; border: 1px solid var(--color-border); border-radius: 4px;
  background: var(--color-surface); color: var(--color-text);
}
.send-results { margin-top: 0.5rem; }
.checkbox-label { display: flex; align-items: center; gap: 0.3rem; }
</style>
