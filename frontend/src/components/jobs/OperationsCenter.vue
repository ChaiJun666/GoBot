<script setup lang="ts">
import { useI18n } from "vue-i18n";

defineProps<{
  title?: string;
  description?: string;
}>();

const { t } = useI18n();
</script>

<template>
  <section class="operations-center">
    <header class="panel panel-detail">
      <div class="panel-heading">
        <p class="panel-kicker">{{ t("jobs.centerKicker") }}</p>
        <h2>{{ title ?? t("jobs.centerTitle") }}</h2>
      </div>
      <p class="drawer-copy">
        {{ description ?? t("jobs.centerDescription") }}
      </p>
    </header>

    <div class="view-grid">
      <slot />
    </div>
  </section>
</template>
