/**
 * 全局类型定义：与后端接口返回结构对齐。
 */

export interface User {
  id: number
  name: string
  email: string
  role: string
  status: 'active' | 'disabled'
  createdAt: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

export interface DashboardSummary {
  totalUsers: number
  totalAgents: number
  totalModels: number
  totalPrompts: number
  activeToday: number
  trend: Array<{ date: string; count: number }>
}

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}
