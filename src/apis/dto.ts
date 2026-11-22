import type { PageResult, Permission, Role, User } from '@/types'

/**
 * 后端 DTO 与映射：FastAPI 返回 snake_case，页面消费 camelCase。
 * 所有字段差异集中在此文件，页面与 store 不感知后端命名。
 */

export interface BackendPage<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface BackendRoleBrief {
  id: number
  code: string
  name: string
}

export interface BackendUser {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  data_scope: string
  created_at: string | null
  roles?: BackendRoleBrief[]
}

export interface BackendPermissionBrief {
  id: number
  code: string
  name: string
}

export interface BackendRole {
  id: number
  code: string
  name: string
  description: string | null
  created_at: string | null
  permissions: BackendPermissionBrief[]
}

export interface BackendPermission {
  id: number
  code: string
  name: string
  module: string
  description: string | null
  created_at: string | null
}

export interface BackendDashboardStats {
  total_users: number
  total_roles: number
  total_permissions: number
}

/** 内置角色：后端仅保护 super_admin（不可删除） */
export const SYSTEM_ROLE_CODES = new Set(['super_admin'])

function normalizeDate(value: string | null | undefined): string {
  if (!value) return ''
  return value.replace('T', ' ').slice(0, 19)
}

export function toUser(dto: BackendUser): User {
  return {
    id: dto.id,
    username: dto.username,
    email: dto.email,
    isActive: dto.is_active,
    isSuperuser: dto.is_superuser,
    dataScope: dto.data_scope,
    roleIds: (dto.roles ?? []).map((role) => role.id),
    createdAt: normalizeDate(dto.created_at),
  }
}

export function toRole(dto: BackendRole): Role {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    description: dto.description ?? '',
    isSystem: SYSTEM_ROLE_CODES.has(dto.code),
    permissionCodes: (dto.permissions ?? []).map((permission) => permission.code),
    createdAt: normalizeDate(dto.created_at),
  }
}

export function toPermission(dto: BackendPermission): Permission {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    module: dto.module,
    description: dto.description ?? '',
    createdAt: normalizeDate(dto.created_at),
  }
}

export function toPage<TDto, TModel>(
  page: BackendPage<TDto>,
  map: (dto: TDto) => TModel,
): PageResult<TModel> {
  return {
    list: page.items.map(map),
    total: page.total,
    page: page.page,
    pageSize: page.page_size,
  }
}
