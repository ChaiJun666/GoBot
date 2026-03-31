<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import InlineStatusNotice from "@/components/InlineStatusNotice.vue";
import type { SiteDeployment, SiteSummary } from "@/types";

const props = defineProps<{
  site: SiteSummary;
  deployments: SiteDeployment[];
  busy: boolean;
}>();

const emit = defineEmits<{
  deploy: [siteId: string];
  edit: [site: SiteSummary];
  delete: [siteId: string];
}>();

const { t } = useI18n();
const showLog = ref(false);

const canDeploy = computed(
  () => !props.busy && ["draft", "error", "stopped"].includes(props.site.status),
);

const deployLabel = computed(() => {
  if (props.busy) return t("sites.deploying");
  return props.site.status === "draft" ? t("sites.deploy") : t("sites.redeploy");
});

const statusBadge = computed(() => {
  const map: Record<string, string> = {
    draft: "queued",
    deploying: "running",
    running: "completed",
    stopped: "failed",
    error: "failed",
  };
  return map[props.site.status] ?? "queued";
});

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}
</script>

<template>
  <div class="panel-toolbar">
    <div class="panel-heading">
      <p class="panel-kicker">{{ t("sites.detailKicker") }}</p>
      <h2>{{ site.display_name }}</h2>
    </div>
    <div class="panel-actions">
      <span class="status-badge" :data-status="statusBadge">{{ t(`sites.siteStatus.${site.status}`) }}</span>
      <button v-if="canDeploy" class="action-button" type="button" @click="$emit('deploy', site.id)">
        {{ deployLabel }}
      </button>
      <button class="ghost-button" type="button" @click="$emit('edit', site)">
        {{ t("sites.editSite") }}
      </button>
      <button class="ghost-button danger-ghost" type="button" @click="$emit('delete', site.id)">
        {{ t("sites.deleteSite") }}
      </button>
    </div>
  </div>

  <dl class="detail-grid">
    <div><dt>{{ t("sites.domain") }}</dt><dd>{{ site.domain }}</dd></div>
    <div><dt>{{ t("sites.serverIp") }}</dt><dd>{{ site.server_ip }}</dd></div>
    <div><dt>{{ t("sites.sshUser") }}</dt><dd>{{ site.ssh_user }}</dd></div>
    <div><dt>{{ t("sites.wpAdminEmail") }}</dt><dd>{{ site.wp_admin_email }}</dd></div>
    <div><dt>{{ t("sites.sslMode") }}</dt><dd>{{ t(`sites.sslModes.${site.ssl_mode}`) }}</dd></div>
    <div v-if="site.site_url"><dt>{{ t("sites.siteUrl") }}</dt><dd><a :href="site.site_url" target="_blank">{{ site.site_url }}</a></dd></div>
    <div v-if="site.wp_admin_url"><dt>{{ t("sites.wpAdminUrl") }}</dt><dd><a :href="site.wp_admin_url" target="_blank">{{ site.wp_admin_url }}</a></dd></div>
    <div v-if="site.deployed_at"><dt>{{ t("sites.deployedAt") }}</dt><dd>{{ formatDate(site.deployed_at) }}</dd></div>
    <div v-if="site.note"><dt>{{ t("sites.note") }}</dt><dd>{{ site.note }}</dd></div>
  </dl>

  <!-- Deploy log -->
  <div v-if="site.deploy_log" class="deploy-log-section">
    <button class="ghost-button" type="button" @click="showLog = !showLog">
      {{ showLog ? t("actions.close") : t("sites.viewLog") }}
    </button>
    <pre v-if="showLog" class="deploy-log">{{ site.deploy_log }}</pre>
  </div>

  <!-- Deployment history -->
  <div v-if="deployments.length" class="deploy-log-section">
    <h3 style="font-size:0.8rem;font-weight:600;margin-bottom:0.5rem;">{{ t("sites.deployments") }}</h3>
    <div class="deployment-list">
      <div v-for="dep in deployments" :key="dep.id" class="deployment-item">
        <span class="status-badge" :data-status="dep.status === 'completed' ? 'completed' : dep.status === 'failed' ? 'failed' : 'queued'">
          {{ dep.status }}
        </span>
        <span class="job-meta">{{ formatDate(dep.created_at) }}</span>
        <span v-if="dep.completed_at" class="job-meta">→ {{ formatDate(dep.completed_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.deploy-log-section { margin-top: 0.75rem; }
.deployment-list { display: flex; flex-direction: column; gap: 0.35rem; }
.deployment-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.78rem; padding: 0.25rem 0; border-bottom: 1px solid var(--color-border); }
.deployment-item:last-child { border-bottom: none; }
.deploy-log {
  background: var(--color-surface,);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0.75rem;
  font-size: 0.75rem;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 0.5rem;
}
.danger-ghost { color: var(--color-danger); }
.danger-ghost:hover { background: var(--color-danger); color: white; }
</style>
