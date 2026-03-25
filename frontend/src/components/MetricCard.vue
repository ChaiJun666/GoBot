<script setup lang="ts">
defineProps<{
  eyebrow: string;
  value: string | number;
  detail: string;
}>();
</script>

<template>
  <article class="metric-card">
    <p class="metric-eyebrow">{{ eyebrow }}</p>
    <p class="metric-value">{{ value }}</p>
    <p class="metric-detail">{{ detail }}</p>
  </article>
</template>
