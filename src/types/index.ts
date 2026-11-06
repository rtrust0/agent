/**
 * 全局类型定义：与后端接口返回结构对齐（RBAC 模块）。
 */

export type PermissionModule = 'user' | 'role' | 'permission' | 'system'

export interface User {
  id: number
  username: string
  email: string
  isActive: boolean
  isSuperuser: boolean
  roleIds: number[]
  createdAt: string
}

export interface Role {
  id: number
  code: string
  name: string
  description: string
  isSystem: boolean
  permissionCodes: string[]
  createdAt: string
}

export interface Permission {
  id: number
  code: string
  name: string
  module: PermissionModule
  createdAt: string
}

export interface AuthSession {
  token: string
  user: User
}

export interface Captcha {
  captchaId: string
  text: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

export interface DashboardSummary {
  totalUsers: number
  totalRoles: number
  totalPermissions: number
}

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}
