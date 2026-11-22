import { get } from './http'
import type { BackendDashboardStats } from './dto'
import type { DashboardSummary } from '@/types'

/** 工作台相关接口（对接 FastAPI：/api/v1/dashboard/stats） */
export const dashboardApi = {
  /** 获取工作台统计概览 */
  async summary(): Promise<DashboardSummary> {
    const stats = await get<BackendDashboardStats>('/dashboard/stats')
    return {
      totalUsers: stats.total_users,
      totalRoles: stats.total_roles,
      totalPermissions: stats.total_permissions,
    }
  },
}
