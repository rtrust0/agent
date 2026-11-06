<script setup lang="ts">
withDefaults(defineProps<{ rows?: number }>(), { rows: 4 })
</script>

<template>
  <div class="skeleton" aria-busy="true" aria-label="加载中">
    <div v-for="row in rows" :key="row" class="skeleton__row" />
  </div>
</template>

<style scoped>
.skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0;
}
.skeleton__row {
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(90deg, #eef1f5 25%, #f7f9fb 37%, #eef1f5 63%);
  background-size: 400% 100%;
  animation: skeleton-shimmer 1.4s ease infinite;
}
@keyframes skeleton-shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}
</style>
