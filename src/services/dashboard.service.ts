import { dashboardApi } from '@/apis/dashboard'
import type { DashboardSummary } from '@/types'

/**
 * 仪表盘业务逻辑层：获取概览数据并可做二次加工。
 */
export const dashboardService = {
  /** 获取仪表盘概览，返回原始数据 */
  async summary(): Promise<DashboardSummary> {
    return dashboardApi.summary()
  },

  /** 业务加工示例：计算近 7 日累计活跃量 */
  async totalActiveLast7Days(): Promise<number> {
    const summary = await dashboardApi.summary()
    return summary.trend.reduce((sum, item) => sum + item.count, 0)
  },
}
