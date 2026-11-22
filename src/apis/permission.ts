import { del, get, post, put } from './http'
import { toPage, toPermission, type BackendPage, type BackendPermission } from './dto'
import { toPageQuery, type PageParams } from './user'
import type { PageResult, Permission, PermissionModule } from '@/types'

export type CreatePermissionData = {
  code: string
  name: string
  /** 后端由权限码前缀派生模块，此字段仅用于页面校验提示 */
  module?: PermissionModule
}

export type UpdatePermissionData = {
  name?: string
  description?: string
  /** 后端不支持修改模块（由 code 决定），保留字段以兼容页面表单 */
  module?: PermissionModule
}

/** 权限相关接口（对接 FastAPI：/api/v1/permissions） */
export const permissionApi = {
  /** 全量权限（供分配权限 / 权限矩阵使用） */
  async listAll(): Promise<Permission[]> {
    const permissions = await get<BackendPermission[]>('/permissions/')
    return permissions.map(toPermission)
  },

  /** 分页搜索权限 */
  async search(params: PageParams): Promise<PageResult<Permission>> {
    const page = await get<BackendPage<BackendPermission>>(
      '/permissions/search',
      toPageQuery(params),
    )
    return toPage(page, toPermission)
  },

  /** 权限详情 */
  async detail(id: number): Promise<Permission> {
    return toPermission(await get<BackendPermission>(`/permissions/${id}`))
  },

  /** 创建权限（module 由后端根据 code 前缀派生） */
  async create(data: CreatePermissionData): Promise<Permission> {
    const created = await post<BackendPermission>('/permissions', {
      code: data.code,
      name: data.name,
    })
    return toPermission(created)
  },

  /** 更新权限（code 不可修改） */
  async update(id: number, data: UpdatePermissionData): Promise<Permission> {
    const payload: Record<string, unknown> = {}
    if (data.name !== undefined) payload.name = data.name
    if (data.description !== undefined) payload.description = data.description
    return toPermission(await put<BackendPermission>(`/permissions/${id}`, payload))
  },

  /** 删除权限 */
  remove(id: number): Promise<null> {
    return del<null>(`/permissions/${id}`)
  },
}
