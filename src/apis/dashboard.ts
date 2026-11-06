import { get } from './http'
import type { DashboardSummary } from '@/types'

/** 工作台相关接口 */
export const dashboardApi = {
  /** 获取工作台统计概览 */
  summary(): Promise<DashboardSummary> {
    return get<DashboardSummary>('/dashboard/summary')
  },
}
