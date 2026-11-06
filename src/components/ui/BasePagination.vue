<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ page: number; pageSize: number; total: number }>()
const emit = defineEmits<{ change: [page: number] }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

function go(target: number) {
  if (target < 1 || target > totalPages.value || target === props.page) return
  emit('change', target)
}
</script>

<template>
  <div class="pagination">
    <span class="pagination__info">共 {{ total }} 条 · 第 {{ page }}/{{ totalPages }} 页</span>
    <div class="pagination__actions">
      <button class="pagination__btn" type="button" :disabled="page <= 1" @click="go(page - 1)">
        上一页
      </button>
      <button class="pagination__btn" type="button" :disabled="page >= totalPages" @click="go(page + 1)">
        下一页
      </button>
    </div>
  </div>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  border-top: 1px solid var(--line);
}
.pagination__info {
  color: var(--ink-2);
  font-size: 12.5px;
}
.pagination__actions {
  display: flex;
  gap: 8px;
}
.pagination__btn {
  height: 30px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink-2);
  font-size: 12.5px;
}
.pagination__btn:hover:not(:disabled) {
  background: #f3f5f8;
}
.pagination__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
