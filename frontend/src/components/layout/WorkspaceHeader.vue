<script setup lang="ts">
import type { AppLocale } from "@/lib/i18n";

interface LocaleOption {
  value: AppLocale;
  label: string;
}

defineProps<{
  title: string;
  subtitle: string;
  activeLocale: AppLocale;
  localeOptions: LocaleOption[];
  actionLabel: string;
}>();

defineEmits<{
  changeLocale: [locale: AppLocale];
  action: [];
}>();
</script>

<template>
  <header class="workspace-header">
    <div>
      <p class="hero-kicker">GoBot Console</p>
      <h1>{{ title }}</h1>
      <p class="hero-copy">{{ subtitle }}</p>
    </div>

    <div class="workspace-actions">
      <div class="locale-switcher" role="group" aria-label="Language switcher">
        <button
          v-for="option in localeOptions"
          :key="option.value"
          class="ghost-button locale-button"
          :class="{ active: option.value === activeLocale }"
          type="button"
          @click="$emit('changeLocale', option.value)"
        >
          {{ option.label }}
        </button>
      </div>

      <button class="action-button" type="button" @click="$emit('action')">
        {{ actionLabel }}
      </button>
    </div>
  </header>
</template>
