<script setup lang="ts">
import type { ConsoleView } from "@/composables/useConsoleWorkspace";

interface NavItem {
  value: ConsoleView;
  label: string;
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
      {{ item.label }}
    </button>
  </nav>
</template>
