<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useDashboardStore } from '@/store/dashboard'

const dashboardStore = useDashboardStore()
const { summary, loading, error } = storeToRefs(dashboardStore)

onMounted(() => {
  dashboardStore.fetchSummary()
})

const statCards = [
  { key: 'totalUsers', label: '用户总数' },
  { key: 'totalAgents', label: 'Agent 数量' },
  { key: 'totalModels', label: '模型数量' },
  { key: 'totalPrompts', label: 'Prompt 数量' },
] as const
</script>

<template>
  <main class="page">
    <h1 class="page__title">仪表盘概览</h1>

    <div v-if="loading" class="skeleton">加载中…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else-if="summary">
      <section class="stat-grid">
        <article v-for="card in statCards" :key="card.key" class="stat-card">
          <span class="stat-card__label">{{ card.label }}</span>
          <span class="stat-card__value">{{ summary[card.key] }}</span>
        </article>
      </section>

      <section class="panel">
        <h2 class="panel__title">近 7 日活跃趋势</h2>
        <div class="trend">
          <div v-for="item in summary.trend" :key="item.date" class="trend__col">
            <div class="trend__bar" :style="{ height: `${item.count * 3}px` }" :title="`${item.date}: ${item.count}`" />
            <span class="trend__date">{{ item.date.slice(5) }}</span>
          </div>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}
.page__title {
  font-size: 28px;
  letter-spacing: -0.03em;
  margin-bottom: 24px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #fff;
}
.stat-card__label {
  font-size: 13px;
  color: #6b7280;
}
.stat-card__value {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.panel {
  margin-top: 24px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #fff;
}
.panel__title {
  font-size: 16px;
  margin-bottom: 16px;
}
.trend {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  height: 120px;
}
.trend__col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.trend__bar {
  width: 100%;
  max-width: 48px;
  background: #4338ca;
  border-radius: 6px 6px 0 0;
}
.trend__date {
  font-size: 12px;
  color: #6b7280;
}
.skeleton,
.error {
  padding: 40px;
  text-align: center;
  color: #6b7280;
  border: 1px dashed #d1d5db;
  border-radius: 16px;
}
.error {
  color: #b91c1c;
  border-color: #fca5a5;
}
@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
