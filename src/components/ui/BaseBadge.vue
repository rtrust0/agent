<script setup lang="ts">
defineProps<{ tone: 'grant' | 'dawn' | 'danger' | 'muted'; text: string }>()
</script>

<template>
  <span class="badge" :class="`badge--${tone}`">{{ text }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 500;
  white-space: nowrap;
}
.badge--grant {
  background: var(--grant-weak);
  color: var(--grant);
}
.badge--dawn {
  background: var(--dawn-weak);
  color: #a6761f;
}
.badge--danger {
  background: var(--danger-weak);
  color: var(--danger);
}
.badge--muted {
  background: #eef1f5;
  color: var(--ink-2);
}
</style>
