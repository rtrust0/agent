<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'danger' | 'ghost'
    disabled?: boolean
    loading?: boolean
    type?: 'button' | 'submit'
  }>(),
  { variant: 'primary', disabled: false, loading: false, type: 'button' },
)
</script>

<template>
  <button
    :type="type"
    class="btn"
    :class="`btn--${variant}`"
    :disabled="disabled || loading"
  >
    <span v-if="loading" class="btn__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 34px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  transition: transform 0.1s ease, background-color 0.15s ease, border-color 0.15s ease;
}
.btn:active:not(:disabled) {
  transform: scale(0.98);
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn--primary {
  background: var(--brand);
  color: #fff;
}
.btn--primary:hover:not(:disabled) {
  background: #3355c7;
}
.btn--danger {
  background: var(--danger);
  color: #fff;
}
.btn--danger:hover:not(:disabled) {
  background: #a93a32;
}
.btn--ghost {
  background: transparent;
  color: var(--ink-2);
  border-color: var(--line);
}
.btn--ghost:hover:not(:disabled) {
  background: #f3f5f8;
}
.btn__spinner {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: btn-spin 0.7s linear infinite;
}
@keyframes btn-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
