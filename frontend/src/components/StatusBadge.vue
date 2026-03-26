<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";

import type { ScrapeJobStatus } from "@/types";

const props = defineProps<{
  status: ScrapeJobStatus;
}>();

const { t } = useI18n();

const label = computed(() => t(`status.${props.status}`));
</script>

<template>
  <span class="status-badge" :data-status="status">{{ label }}</span>
</template>
