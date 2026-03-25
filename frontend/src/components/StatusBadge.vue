<script setup lang="ts">
import { computed } from "vue";

import type { ScrapeJobStatus } from "@/types";

const props = defineProps<{
  status: ScrapeJobStatus;
}>();

const label = computed(() => props.status.replace("_", " "));
</script>

<template>
  <span class="status-badge" :data-status="status">{{ label }}</span>
</template>
