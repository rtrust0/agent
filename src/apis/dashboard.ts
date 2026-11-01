import { get } from './http'
import type { DashboardSummary } from '@/types'

/** 仪表盘相关接口 */
export const dashboardApi = {
  /** 获取仪表盘概览统计 */
  summary(): Promise<DashboardSummary> {
    return get<DashboardSummary>('/dashboard/summary')
  },
}
