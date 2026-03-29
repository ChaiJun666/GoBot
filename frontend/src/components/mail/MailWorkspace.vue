<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import type {
  CreateMailboxRequest,
  LeadRecipientSummary,
  MailFolder,
  MailMessageDetail,
  MailMessageSummary,
  MailProviderConfig,
  MailProviderKey,
  MailboxSummary,
  SendMailRequest,
  UpdateMailboxRequest,
} from "@/types";

const props = defineProps<{
  mailboxes: MailboxSummary[];
  providers: MailProviderConfig[];
  selectedMailboxId: string | null;
  folder: MailFolder;
  messages: MailMessageSummary[];
  selectedMessage: MailMessageDetail | null;
  leadRecipients: LeadRecipientSummary[];
  composerOpen: boolean;
  loadingMailboxes: boolean;
  loadingMessages: boolean;
  loadingMessageDetail: boolean;
  savingMailbox: boolean;
  sendingMail: boolean;
  syncingMailboxId: string | null;
  inboxCount: number;
  sentCount: number;
  hasMore: boolean;
  loadingMore: boolean;
}>();

const emit = defineEmits<{
  selectMailbox: [mailboxId: string];
  selectFolder: [folder: MailFolder];
  selectMessage: [messageId: string];
  createMailbox: [payload: CreateMailboxRequest];
  updateMailbox: [mailboxId: string, payload: UpdateMailboxRequest];
  syncMailbox: [mailboxId: string];
  sendMail: [payload: SendMailRequest];
  updateComposerOpen: [value: boolean];
  loadMore: [];
}>();

const { t, tm } = useI18n();

function providerLabel(provider: string): string {
  const providers = tm("mail.providers") as Record<string, string>;
  return providers[provider] ?? provider;
}

const mailboxForm = reactive({
  provider: "gmail" as MailProviderKey,
  email_address: "",
  auth_secret: "",
  note: "",
});
const composeForm = reactive({
  recipientsText: "",
  subject: "",
  body: "",
});
const selectedLeadId = ref<string>("");
const editingMailboxId = ref<string | null>(null);

const selectedMailbox = computed(
  () => props.mailboxes.find((mailbox) => mailbox.id === props.selectedMailboxId) ?? null,
);
const selectedLead = computed(
  () => props.leadRecipients.find((recipient) => recipient.id === selectedLeadId.value) ?? null,
);
const syncingSelectedMailbox = computed(
  () => props.syncingMailboxId !== null && props.syncingMailboxId === props.selectedMailboxId,
);
const hasMessages = computed(() => props.messages.length > 0);

watch(
  () => props.selectedMailboxId,
  () => {
    composeForm.recipientsText = "";
    composeForm.subject = "";
    composeForm.body = "";
    emit("updateComposerOpen", false);
  },
);

function startCreateMailbox() {
  editingMailboxId.value = null;
  mailboxForm.provider = "gmail";
  mailboxForm.email_address = "";
  mailboxForm.auth_secret = "";
  mailboxForm.note = "";
}

function startEditMailbox(mailbox: MailboxSummary) {
  editingMailboxId.value = mailbox.id;
  mailboxForm.provider = mailbox.provider;
  mailboxForm.email_address = mailbox.email_address;
  mailboxForm.auth_secret = "";
  mailboxForm.note = mailbox.note ?? "";
}

function submitMailboxForm() {
  if (editingMailboxId.value) {
    emit("updateMailbox", editingMailboxId.value, {
      note: mailboxForm.note.trim() || null,
      auth_secret: mailboxForm.auth_secret.trim() || null,
    });
    return;
  }

  emit("createMailbox", {
    provider: mailboxForm.provider,
    email_address: mailboxForm.email_address.trim(),
    auth_secret: mailboxForm.auth_secret.trim(),
    note: mailboxForm.note.trim() || null,
  });
}

function addLeadRecipient() {
  if (!selectedLead.value) {
    return;
  }

  const items = parseRecipients(composeForm.recipientsText);
  if (!items.includes(selectedLead.value.email)) {
    items.push(selectedLead.value.email);
  }
  composeForm.recipientsText = items.join(", ");
  selectedLeadId.value = "";
}

function submitMail() {
  if (!selectedMailbox.value) {
    return;
  }

  emit("sendMail", {
    mailbox_id: selectedMailbox.value.id,
    to: parseRecipients(composeForm.recipientsText),
    subject: composeForm.subject.trim(),
    body: composeForm.body.trim(),
  });
}

function parseRecipients(value: string): string[] {
  return value
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatDate(value: string | null): string {
  if (!value) {
    return t("common.pending");
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function messageCounter(folder: MailFolder): string {
  const count = folder === "inbox" ? props.inboxCount : props.sentCount;
  return t("mail.messageCount", { count });
}

function onMessageListScroll(event: Event) {
  const el = event.target as HTMLElement;
  if (!el) return;
  const threshold = 50;
  if (el.scrollHeight - el.scrollTop - el.clientHeight < threshold && props.hasMore && !props.loadingMore) {
    emit("loadMore");
  }
}
</script>

<template>
  <section class="mail-workspace">
    <section class="panel mail-sidebar">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("mail.accountsKicker") }}</p>
          <h2>{{ t("mail.accountsTitle") }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="startCreateMailbox">
          {{ t("mail.addMailbox") }}
        </button>
      </div>

      <div v-if="mailboxes.length" class="mailbox-list">
        <button
          v-for="mailbox in mailboxes"
          :key="mailbox.id"
          class="mailbox-card"
          :class="{ selected: mailbox.id === selectedMailboxId }"
          type="button"
          @click="$emit('selectMailbox', mailbox.id)"
        >
          <div class="mailbox-card-top">
            <strong>{{ mailbox.note || mailbox.email_address }}</strong>
            <span class="status-badge" :data-status="mailbox.status === 'ready' ? 'completed' : 'failed'">
              {{ mailbox.status === "ready" ? t("mail.connected") : t("mail.error") }}
            </span>
          </div>
          <p class="job-meta">{{ mailbox.email_address }}</p>
          <p class="job-meta">{{ providerLabel(mailbox.provider) }}</p>
          <p class="job-meta">{{ t("mail.lastSynced") }}: {{ formatDate(mailbox.last_synced_at) }}</p>
        </button>
      </div>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("mail.noMailboxesTitle") }}</p>
        <span>{{ t("mail.noMailboxesDescription") }}</span>
      </div>

      <form class="composer-form" @submit.prevent="submitMailboxForm">
        <div class="panel-heading">
          <p class="panel-kicker">
            {{ editingMailboxId ? t("mail.editMailboxKicker") : t("mail.createMailboxKicker") }}
          </p>
          <h2>{{ editingMailboxId ? t("mail.editMailboxTitle") : t("mail.createMailboxTitle") }}</h2>
        </div>

        <label>
          <span>{{ t("mail.provider") }}</span>
          <select v-model="mailboxForm.provider" :disabled="Boolean(editingMailboxId)">
            <option v-for="provider in providers" :key="provider.key" :value="provider.key">
              {{ provider.label }}
            </option>
          </select>
        </label>

        <label>
          <span>{{ t("mail.emailAddress") }}</span>
          <input
            v-model="mailboxForm.email_address"
            type="email"
            autocomplete="username"
            :disabled="Boolean(editingMailboxId)"
          />
        </label>

        <label>
          <span>{{ t("mail.authSecret") }}</span>
          <input v-model="mailboxForm.auth_secret" type="password" autocomplete="current-password" />
        </label>

        <label>
          <span>{{ t("mail.note") }}</span>
          <input v-model="mailboxForm.note" type="text" maxlength="120" />
        </label>

        <div class="panel-actions">
          <button class="action-button" type="submit" :disabled="savingMailbox">
            {{
              savingMailbox
                ? t("mail.savingMailbox")
                : editingMailboxId
                  ? t("mail.saveMailbox")
                  : t("mail.connectMailbox")
            }}
          </button>
          <button
            v-if="selectedMailbox"
            class="ghost-button"
            type="button"
            @click="startEditMailbox(selectedMailbox)"
          >
            {{ t("mail.editMailbox") }}
          </button>
        </div>
      </form>
    </section>

    <section class="panel mail-list-panel">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("mail.messagesKicker") }}</p>
          <h2>{{ selectedMailbox ? selectedMailbox.email_address : t("mail.messagesTitle") }}</h2>
        </div>
        <div class="panel-actions">
          <button
            class="ghost-button"
            type="button"
            :disabled="!selectedMailbox || syncingSelectedMailbox"
            @click="selectedMailbox && $emit('syncMailbox', selectedMailbox.id)"
          >
            {{
              syncingSelectedMailbox
                ? t("mail.syncing")
                : t("mail.refreshMailbox")
            }}
          </button>
          <button
            class="action-button"
            type="button"
            :disabled="!selectedMailbox"
            @click="$emit('updateComposerOpen', true)"
          >
            {{ t("mail.compose") }}
          </button>
        </div>
      </div>

      <div v-if="selectedMailbox" class="mail-folder-tabs">
        <button
          class="mail-folder-tab"
          :class="{ active: folder === 'inbox' }"
          type="button"
          @click="$emit('selectFolder', 'inbox')"
        >
          {{ t("mail.inbox") }}
          <span>{{ messageCounter("inbox") }}</span>
        </button>
        <button
          class="mail-folder-tab"
          :class="{ active: folder === 'sent' }"
          type="button"
          @click="$emit('selectFolder', 'sent')"
        >
          {{ t("mail.sent") }}
          <span>{{ messageCounter("sent") }}</span>
        </button>
      </div>

      <div v-if="selectedMailbox && hasMessages" class="mail-message-list" @scroll="onMessageListScroll">
        <button
          v-for="message in messages"
          :key="message.id"
          class="mail-message-item"
          :class="{ selected: message.id === selectedMessage?.id }"
          type="button"
          @click="$emit('selectMessage', message.id)"
        >
          <div class="mail-message-item-top">
            <strong>{{ message.subject }}</strong>
            <span>{{ formatDate(message.received_at || message.sent_at) }}</span>
          </div>
          <p class="job-meta">
            {{
              folder === "inbox"
                ? (message.from_name || message.from_address || t("common.unknown"))
                : (message.to_summary || t("common.unavailable"))
            }}
          </p>
          <p class="job-meta">{{ message.snippet || t("mail.noSnippet") }}</p>
        </button>
        <div v-if="loadingMore" class="mail-load-more">{{ t("mail.loadingMore") }}</div>
        <div v-else-if="!hasMore && messages.length > 0" class="mail-no-more">{{ t("mail.noMore") }}</div>
      </div>
      <div v-else-if="selectedMailbox" class="empty-state compact-empty">
        <p>{{ loadingMessages ? t("mail.loadingMessages") : t("mail.emptyFolderTitle") }}</p>
        <span>{{ t("mail.emptyFolderDescription") }}</span>
      </div>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("mail.selectMailboxTitle") }}</p>
        <span>{{ t("mail.selectMailboxDescription") }}</span>
      </div>
    </section>

    <section class="panel mail-detail-panel">
      <template v-if="composerOpen">
        <div class="panel-toolbar">
          <div class="panel-heading">
            <p class="panel-kicker">{{ t("mail.composeKicker") }}</p>
            <h2>{{ t("mail.composeTitle") }}</h2>
          </div>
          <button class="ghost-button" type="button" @click="$emit('updateComposerOpen', false)">
            {{ t("actions.close") }}
          </button>
        </div>

        <form class="composer-form" @submit.prevent="submitMail">
          <label>
            <span>{{ t("mail.fromMailbox") }}</span>
            <input :value="selectedMailbox?.email_address ?? ''" type="text" disabled />
          </label>

          <div class="composer-grid">
            <label>
              <span>{{ t("mail.leadRecipient") }}</span>
              <select v-model="selectedLeadId">
                <option value="">{{ t("mail.selectLeadRecipient") }}</option>
                <option v-for="recipient in leadRecipients" :key="recipient.id" :value="recipient.id">
                  {{ recipient.lead_name }} · {{ recipient.email }}
                </option>
              </select>
            </label>

            <div class="panel-actions mail-inline-action">
              <button class="ghost-button" type="button" @click="addLeadRecipient">
                {{ t("mail.addRecipient") }}
              </button>
            </div>
          </div>

          <label>
            <span>{{ t("mail.recipients") }}</span>
            <textarea
              v-model="composeForm.recipientsText"
              rows="3"
              :placeholder="t('mail.recipientsPlaceholder')"
            />
          </label>

          <label>
            <span>{{ t("mail.subject") }}</span>
            <input v-model="composeForm.subject" type="text" maxlength="255" />
          </label>

          <label>
            <span>{{ t("mail.body") }}</span>
            <textarea v-model="composeForm.body" rows="10" />
          </label>

          <InlineStatusNotice
            v-if="!selectedMailbox"
            :title="t('mail.selectMailboxTitle')"
            :detail="t('mail.selectMailboxDescription')"
            tone="warning"
          />

          <div class="panel-actions">
            <button class="action-button" type="submit" :disabled="!selectedMailbox || sendingMail">
              {{ sendingMail ? t("mail.sending") : t("mail.send") }}
            </button>
          </div>
        </form>
      </template>

      <template v-else-if="selectedMessage">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("mail.detailKicker") }}</p>
          <h2>{{ selectedMessage.subject }}</h2>
        </div>

        <dl class="detail-grid">
          <div>
            <dt>{{ t("mail.from") }}</dt>
            <dd>{{ selectedMessage.from_name || selectedMessage.from_address || t("common.unknown") }}</dd>
          </div>
          <div>
            <dt>{{ t("mail.to") }}</dt>
            <dd>{{ selectedMessage.to_summary || t("common.unavailable") }}</dd>
          </div>
          <div>
            <dt>{{ t("mail.folder") }}</dt>
            <dd>{{ selectedMessage.folder === "inbox" ? t("mail.inbox") : t("mail.sent") }}</dd>
          </div>
          <div>
            <dt>{{ t("mail.date") }}</dt>
            <dd>{{ formatDate(selectedMessage.received_at || selectedMessage.sent_at) }}</dd>
          </div>
        </dl>

        <article class="mail-message-body">
          <pre>{{ loadingMessageDetail ? t("mail.loadingMessageDetail") : (selectedMessage.body_text || t("mail.emptyBody")) }}</pre>
        </article>
      </template>

      <div v-else class="empty-state compact-empty">
        <p>{{ t("mail.emptyDetailTitle") }}</p>
        <span>{{ t("mail.emptyDetailDescription") }}</span>
      </div>
    </section>
  </section>
</template>
