<script setup lang="ts">
import type { ConsoleView } from "@/composables/useConsoleWorkspace";
import type { AppLocale } from "@/lib/i18n";

import PrimaryNav from "@/components/layout/PrimaryNav.vue";
import WorkspaceHeader from "@/components/layout/WorkspaceHeader.vue";

interface NavItem {
  value: ConsoleView;
  label: string;
  hint?: string;
}

interface LocaleOption {
  value: AppLocale;
  label: string;
}

defineProps<{
  activeView: ConsoleView;
  navItems: NavItem[];
  title: string;
  subtitle: string;
  meta?: string;
  activeLocale: AppLocale;
  localeOptions: LocaleOption[];
  actionLabel: string;
}>();

defineEmits<{
  selectView: [view: ConsoleView];
  changeLocale: [locale: AppLocale];
  action: [];
}>();
</script>

<template>
  <div class="console-layout">
    <aside class="console-sidebar">
      <div class="console-brand">
        <p class="hero-kicker">Workspace</p>
        <strong>GoBot</strong>
      </div>
      <PrimaryNav :active-view="activeView" :items="navItems" @select="$emit('selectView', $event)" />
    </aside>

    <div class="console-main">
      <WorkspaceHeader
        :title="title"
        :subtitle="subtitle"
        :meta="meta"
        :active-locale="activeLocale"
        :locale-options="localeOptions"
        :action-label="actionLabel"
        @change-locale="$emit('changeLocale', $event)"
        @action="$emit('action')"
      />

      <main class="workspace-body">
        <slot />
      </main>
    </div>
  </div>
</template>
