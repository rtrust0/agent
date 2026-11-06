<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'

const props = defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ close: [] }>()

watch(
  () => props.open,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})

function onClose() {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-mask" @click.self="onClose">
      <div class="modal" role="dialog" aria-modal="true" :aria-label="title">
        <header class="modal__head">
          <h3 class="modal__title">{{ title }}</h3>
          <button class="modal__close" type="button" aria-label="关闭" @click="onClose">×</button>
        </header>
        <div class="modal__body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="modal__foot">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 27, 45, 0.45);
}
.modal {
  width: 100%;
  max-width: 520px;
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  background: var(--panel);
  border-radius: 10px;
  box-shadow: 0 24px 64px rgba(15, 27, 45, 0.28);
}
.modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--line);
}
.modal__title {
  font-size: 14px;
  font-weight: 600;
}
.modal__close {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ink-2);
  font-size: 18px;
  line-height: 1;
}
.modal__close:hover {
  background: #f3f5f8;
}
.modal__body {
  padding: 18px;
  overflow: auto;
}
.modal__foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 18px;
  border-top: 1px solid var(--line);
}
</style>
