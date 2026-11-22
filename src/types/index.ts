/**
 * 全局类型定义：与后端接口返回结构对齐（RBAC 模块）。
 * 后端返回 snake_case，apis 层负责映射为这里的 camelCase 领域模型。
 */

/** 权限模块前缀：由权限码 `模块:操作` 派生，后端共 15 个模块 */
export type PermissionModule = string

export interface User {
  id: number
  username: string
  email: string
  isActive: boolean
  isSuperuser: boolean
  dataScope: string
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
  description: string
  createdAt: string
}

export interface AuthSession {
  token: string
  user: User
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
