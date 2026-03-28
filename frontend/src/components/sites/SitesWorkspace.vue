<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import SiteDetailPanel from "@/components/sites/SiteDetailPanel.vue";
import type {
  CreateSiteRequest,
  SiteDeployment,
  SiteSummary,
  SslMode,
  UpdateSiteRequest,
} from "@/types";

const WP_PLUGIN_OPTIONS = [
  "astra", "elementor", "seo-by-rank-math", "wp-super-cache",
  "imagify", "jetpack-boost", "polylang", "contact-form-7", "chaty", "ecommerce-product-catalog",
];

const props = defineProps<{
  sites: SiteSummary[];
  selectedSiteId: string | null;
  loadingSites: boolean;
  busy: boolean;
}>();

const emit = defineEmits<{
  selectSite: [siteId: string];
  createSite: [payload: CreateSiteRequest];
  updateSite: [siteId: string, payload: UpdateSiteRequest];
  deleteSite: [siteId: string];
  deploySite: [siteId: string];
}>();

const { t } = useI18n();

const showForm = ref(false);
const editingId = ref<string | null>(null);
const deletingId = ref<string | null>(null);
const siteDeployments = ref<SiteDeployment[]>([]);

const form = reactive({
  display_name: "",
  domain: "",
  server_ip: "",
  ssh_user: "root",
  ssh_password: "",
  wp_admin_user: "admin",
  wp_admin_password: "",
  wp_admin_email: "",
  mysql_root_password: "",
  ssl_mode: "none" as SslMode,
  cloudflare_zone_id: "",
  cloudflare_api_token: "",
  cloudflare_dns_proxy: false,
  wp_plugins: [] as string[],
  note: "",
});

const selectedSite = computed(
  () => props.sites.find((s) => s.id === props.selectedSiteId) ?? null,
);
const isEditing = computed(() => editingId.value !== null);
const formTitle = computed(() =>
  isEditing.value ? t("sites.editFormTitle") : t("sites.createFormTitle"),
);

const canSubmit = computed(() =>
  form.display_name.trim() !== "" && form.domain.trim() !== "" && form.server_ip.trim() !== "" && form.ssh_password.trim() !== "",
);

function resetForm() {
  editingId.value = null;
  Object.assign(form, {
    display_name: "", domain: "", server_ip: "", ssh_user: "root",
    ssh_password: "", wp_admin_user: "admin", wp_admin_password: "",
    wp_admin_email: "", mysql_root_password: "", ssl_mode: "none" as SslMode,
    cloudflare_zone_id: "", cloudflare_api_token: "", cloudflare_dns_proxy: false,
    wp_plugins: [], note: "",
  });
}

function startCreate() { resetForm(); showForm.value = true; }

function startEdit(site: SiteSummary) {
  editingId.value = site.id;
  Object.assign(form, {
    display_name: site.display_name, domain: site.domain, server_ip: site.server_ip,
    ssh_user: site.ssh_user, ssh_password: "", wp_admin_user: site.wp_admin_user,
    wp_admin_password: "", wp_admin_email: site.wp_admin_email,
    mysql_root_password: "", ssl_mode: site.ssl_mode as SslMode,
    cloudflare_zone_id: site.cloudflare_zone_id ?? "", cloudflare_api_token: "",
    cloudflare_dns_proxy: site.cloudflare_dns_proxy, wp_plugins: [...site.wp_plugins],
    note: site.note ?? "",
  });
  showForm.value = true;
}

function cancelForm() { showForm.value = false; resetForm(); }

function submit() {
  if (isEditing.value && editingId.value) {
    const payload: UpdateSiteRequest = {};
    if (form.display_name.trim()) payload.display_name = form.display_name.trim();
    if (form.domain.trim()) payload.domain = form.domain.trim();
    if (form.server_ip.trim()) payload.server_ip = form.server_ip.trim();
    if (form.ssh_user.trim()) payload.ssh_user = form.ssh_user.trim();
    if (form.ssh_password.trim()) payload.ssh_password = form.ssh_password.trim();
    if (form.wp_admin_email.trim()) payload.wp_admin_email = form.wp_admin_email.trim();
    emit("updateSite", editingId.value, payload);
    return;
  }
  emit("createSite", {
    display_name: form.display_name.trim(),
    domain: form.domain.trim(),
    server_ip: form.server_ip.trim(),
    ssh_user: form.ssh_user.trim() || "root",
    ssh_password: form.ssh_password.trim(),
    wp_admin_email: form.wp_admin_email.trim(),
    mysql_root_password: form.mysql_root_password.trim(),
    wp_admin_user: form.wp_admin_user.trim() || null,
    wp_admin_password: form.wp_admin_password.trim() || null,
    ssl_mode: form.ssl_mode,
    cloudflare_zone_id: form.cloudflare_zone_id.trim() || null,
    cloudflare_api_token: form.cloudflare_api_token.trim() || null,
    cloudflare_dns_proxy: form.cloudflare_dns_proxy,
    wp_plugins: form.wp_plugins.length ? form.wp_plugins : null,
    note: form.note.trim() || null,
  });
}

function togglePlugin(slug: string) {
  const idx = form.wp_plugins.indexOf(slug);
  if (idx >= 0) form.wp_plugins.splice(idx, 1);
  else form.wp_plugins.push(slug);
}

function doDelete() {
  if (deletingId.value) { emit("deleteSite", deletingId.value); deletingId.value = null; }
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "2-digit" }).format(new Date(value));
}

defineExpose({ startCreate, startEdit, cancelForm });
</script>

<template>
  <section class="mail-workspace">
    <!-- Left: site list -->
    <section class="panel mail-sidebar">
      <div class="panel-toolbar">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("sites.listKicker") }}</p>
          <h2>{{ t("sites.listTitle") }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="startCreate">{{ t("sites.addSite") }}</button>
      </div>

      <div v-if="sites.length" class="mailbox-list">
        <button v-for="site in sites" :key="site.id" class="mailbox-card" :class="{ selected: site.id === selectedSiteId }"
          type="button" @click="$emit('selectSite', site.id)">
          <div class="mailbox-card-top">
            <strong>{{ site.display_name }}</strong>
            <span class="status-badge" :data-status="site.status === 'running' ? 'completed' : site.status === 'error' ? 'failed' : 'queued'">
              {{ t(`sites.siteStatus.${site.status}`) }}
            </span>
          </div>
          <p class="job-meta">{{ site.domain }}</p>
          <p class="job-meta">{{ formatDate(site.created_at) }}</p>
        </button>
      </div>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("sites.noSitesTitle") }}</p>
        <span>{{ t("sites.noSitesDescription") }}</span>
      </div>

      <!-- Form -->
      <form v-if="showForm" class="composer-form" @submit.prevent="submit">
        <div class="panel-heading">
          <p class="panel-kicker">{{ t("sites.createFormKicker") }}</p>
          <h2>{{ formTitle }}</h2>
        </div>
        <fieldset><legend>{{ t("sites.sectionBasic") }}</legend>
          <label><span>{{ t("sites.displayName") }} *</span><input v-model="form.display_name" type="text" maxlength="120" /></label>
          <label><span>{{ t("sites.domain") }} *</span><input v-model="form.domain" type="text" placeholder="example.com" /></label>
          <label><span>{{ t("sites.note") }}</span><input v-model="form.note" type="text" maxlength="500" /></label>
        </fieldset>
        <fieldset><legend>{{ t("sites.sectionServer") }}</legend>
          <label><span>{{ t("sites.serverIp") }} *</span><input v-model="form.server_ip" type="text" placeholder="1.2.3.4" /></label>
          <label><span>{{ t("sites.sshUser") }}</span><input v-model="form.ssh_user" type="text" /></label>
          <label><span>{{ t("sites.sshPassword") }} *</span><input v-model="form.ssh_password" type="password" autocomplete="off" /></label>
        </fieldset>
        <fieldset><legend>{{ t("sites.sectionWordPress") }}</legend>
          <label><span>{{ t("sites.wpAdminEmail") }} *</span><input v-model="form.wp_admin_email" type="email" /></label>
          <label><span>{{ t("sites.wpAdminUser") }}</span><input v-model="form.wp_admin_user" type="text" /></label>
          <label><span>{{ t("sites.wpAdminPassword") }}</span><input v-model="form.wp_admin_password" type="password" autocomplete="off" /></label>
        </fieldset>
        <fieldset><legend>{{ t("sites.sectionDatabase") }}</legend>
          <label><span>{{ t("sites.mysqlRootPassword") }} *</span><input v-model="form.mysql_root_password" type="password" autocomplete="off" /></label>
        </fieldset>
        <fieldset><legend>{{ t("sites.sectionSSL") }}</legend>
          <label><span>{{ t("sites.sslMode") }}</span>
            <select v-model="form.ssl_mode">
              <option value="none">{{ t("sites.sslModes.none") }}</option>
              <option value="cloudflare">{{ t("sites.sslModes.cloudflare") }}</option>
            </select>
          </label>
          <template v-if="form.ssl_mode === 'cloudflare'">
            <label><span>{{ t("sites.cfZoneId") }}</span><input v-model="form.cloudflare_zone_id" type="text" /></label>
            <label><span>{{ t("sites.cfApiToken") }}</span><input v-model="form.cloudflare_api_token" type="password" autocomplete="off" /></label>
            <label class="checkbox-label"><input v-model="form.cloudflare_dns_proxy" type="checkbox" /> {{ t("sites.cfDnsProxy") }}</label>
          </template>
        </fieldset>
        <fieldset><legend>{{ t("sites.sectionPlugins") }}</legend>
          <div class="plugin-grid">
            <label v-for="slug in WP_PLUGIN_OPTIONS" :key="slug" class="checkbox-label">
              <input type="checkbox" :checked="form.wp_plugins.includes(slug)" @change="togglePlugin(slug)" />
              {{ slug }}
            </label>
          </div>
        </fieldset>
        <div class="panel-actions">
          <button class="action-button" type="submit" :disabled="!canSubmit || busy">
            {{ busy ? t("sites.saving") : isEditing ? t("sites.saveSite") : t("sites.addSite") }}
          </button>
          <button class="ghost-button" type="button" @click="cancelForm">{{ t("actions.cancel") }}</button>
        </div>
      </form>
    </section>

    <!-- Right: detail -->
    <section class="panel mail-list-panel">
      <template v-if="selectedSite">
        <SiteDetailPanel :site="selectedSite" :deployments="siteDeployments" :busy="busy"
          @deploy="$emit('deploySite', $event)" @edit="startEdit($event)" @delete="deletingId = $event" />
        <div v-if="deletingId === selectedSite.id" class="delete-confirm">
          <InlineStatusNotice :title="t('sites.deleteConfirmTitle')"
            :detail="t('sites.deleteConfirmDescription', { name: selectedSite.display_name })" tone="warning" />
          <div class="panel-actions" style="margin-top:0.5rem">
            <button class="action-button" type="button" @click="doDelete">{{ t("sites.confirmDelete") }}</button>
            <button class="ghost-button" type="button" @click="deletingId = null">{{ t("actions.close") }}</button>
          </div>
        </div>
      </template>
      <div v-else class="empty-state compact-empty">
        <p>{{ t("sites.selectSiteTitle") }}</p>
        <span>{{ t("sites.selectSiteDescription") }}</span>
      </div>
    </section>
  </section>
</template>

<style scoped>
.plugin-grid { display: flex; flex-wrap: wrap; gap: 0.25rem 0.75rem; }
.checkbox-label { display: flex; align-items: center; gap: 0.25rem; font-size: 0.8rem; cursor: pointer; }
.delete-confirm { margin-top: 1rem; }
.danger-ghost { color: var(--color-danger); }
.danger-ghost:hover { background: var(--color-danger); color: white; }
fieldset { border: none; padding: 0; margin: 0 0 0.5rem; }
fieldset legend { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-muted); margin-bottom: 0.25rem; }
</style>
