<script setup lang="ts">
import { useToastItems } from '@/composables/useToast'

const items = useToastItems()
</script>

<template>
  <div class="toast-stack" aria-live="polite">
    <div v-for="item in items" :key="item.id" class="toast" :class="`toast--${item.type}`">
      <span class="toast__dot" aria-hidden="true" />
      <span>{{ item.message }}</span>
    </div>
  </div>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 200px;
  max-width: 360px;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 8px 24px rgba(15, 27, 45, 0.14);
  font-size: 13px;
  color: var(--ink);
}
.toast__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ink-3);
  flex-shrink: 0;
}
.toast--success .toast__dot {
  background: var(--grant);
}
.toast--error .toast__dot {
  background: var(--danger);
}
.toast--info .toast__dot {
  background: var(--brand);
}
</style>
