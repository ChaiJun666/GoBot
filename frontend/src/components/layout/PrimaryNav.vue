<script setup lang="ts">
import type { ConsoleView } from "@/composables/useConsoleWorkspace";

interface NavItem {
  value: ConsoleView;
  label: string;
  hint?: string;
}

defineProps<{
  activeView: ConsoleView;
  items: NavItem[];
}>();

defineEmits<{
  select: [view: ConsoleView];
}>();
</script>

<template>
  <nav class="primary-nav" aria-label="Primary">
    <button
      v-for="item in items"
      :key="item.value"
      class="primary-nav-button"
      :class="{ active: item.value === activeView }"
      type="button"
      @click="$emit('select', item.value)"
    >
      <span class="primary-nav-label">{{ item.label }}</span>
      <span v-if="item.hint" class="primary-nav-hint">{{ item.hint }}</span>
    </button>
  </nav>
</template>
