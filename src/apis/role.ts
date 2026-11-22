import { del, get, post, put } from './http'
import { toPage, toRole, type BackendPage, type BackendPermission, type BackendRole } from './dto'
import { toPageQuery, type PageParams } from './user'
import type { PageResult, Role } from '@/types'

export type CreateRoleData = {
  code: string
  name: string
  description?: string
  permissionCodes?: string[]
}

export type UpdateRoleData = {
  /** 后端不支持修改角色码，保留字段以兼容页面表单 */
  code?: string
  name?: string
  description?: string
}

/** 权限码 → 权限 ID（后端分配权限使用 ID 列表） */
async function resolvePermissionIds(permissionCodes: string[]): Promise<number[]> {
  if (permissionCodes.length === 0) return []
  const permissions = await get<BackendPermission[]>('/permissions/')
  const idByCode = new Map(permissions.map((permission) => [permission.code, permission.id]))
  const ids = permissionCodes.map((code) => idByCode.get(code)).filter((id): id is number => id !== undefined)
  if (ids.length !== permissionCodes.length) {
    const unknown = permissionCodes.filter((code) => !idByCode.has(code))
    throw new Error(`权限码不存在：${unknown.join('、')}`)
  }
  return ids
}

async function assignPermissionCodes(id: number, permissionCodes: string[]): Promise<Role> {
  const permissionIds = await resolvePermissionIds(permissionCodes)
  const role = await put<BackendRole>(`/roles/${id}/permissions`, { permission_ids: permissionIds })
  return toRole(role)
}

/** 角色相关接口（对接 FastAPI：/api/v1/roles） */
export const roleApi = {
  /** 全量角色（供分配角色 / 权限矩阵使用） */
  async listAll(): Promise<Role[]> {
    const roles = await get<BackendRole[]>('/roles/')
    return roles.map(toRole)
  },

  /** 分页搜索角色 */
  async search(params: PageParams): Promise<PageResult<Role>> {
    const page = await get<BackendPage<BackendRole>>('/roles/search', toPageQuery(params))
    return toPage(page, toRole)
  },

  /** 角色详情 */
  async detail(id: number): Promise<Role> {
    return toRole(await get<BackendRole>(`/roles/${id}`))
  },

  /** 创建角色：先建角色，再按权限码分配（后端创建接口不含权限码） */
  async create(data: CreateRoleData): Promise<Role> {
    const created = await post<BackendRole>('/roles', {
      code: data.code,
      name: data.name,
      description: data.description ?? '',
    })
    const permissionCodes = data.permissionCodes ?? []
    if (permissionCodes.length === 0) return toRole(created)
    return assignPermissionCodes(created.id, permissionCodes)
  },

  /** 更新角色（角色码不可修改，后端忽略 code 字段） */
  async update(id: number, data: UpdateRoleData): Promise<Role> {
    const payload: Record<string, unknown> = {}
    if (data.name !== undefined) payload.name = data.name
    if (data.description !== undefined) payload.description = data.description
    return toRole(await put<BackendRole>(`/roles/${id}`, payload))
  },

  /** 删除角色 */
  remove(id: number): Promise<null> {
    return del<null>(`/roles/${id}`)
  },

  /** 给角色分配权限（按权限码） */
  assignPermissions(id: number, permissionCodes: string[]): Promise<Role> {
    return assignPermissionCodes(id, permissionCodes)
  },
}
