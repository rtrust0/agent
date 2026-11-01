import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardService } from '@/services/dashboard.service'
import type { DashboardSummary } from '@/types'

/** 仪表盘状态仓库 */
export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref<DashboardSummary | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchSummary() {
    loading.value = true
    error.value = ''
    try {
      summary.value = await dashboardService.summary()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, error, fetchSummary }
})
