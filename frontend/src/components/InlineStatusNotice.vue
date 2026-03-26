<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title: string;
    detail?: string | null;
    tone?: "info" | "success" | "warning" | "danger";
  }>(),
  {
    detail: null,
    tone: "info",
  },
);
</script>

<template>
  <section class="inline-notice" :data-tone="props.tone" aria-live="polite">
    <p class="inline-notice-title">{{ props.title }}</p>
    <p v-if="props.detail" class="inline-notice-detail">{{ props.detail }}</p>
  </section>
</template>
