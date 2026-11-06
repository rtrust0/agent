import { dashboardApi } from '@/apis/dashboard'
import type { DashboardSummary } from '@/types'

/** 工作台业务逻辑层 */
export const dashboardService = {
  /** 工作台统计概览 */
  summary(): Promise<DashboardSummary> {
    return dashboardApi.summary()
  },
}
