import { del, get, post, put } from './http'
import type { PageResult, Permission, PermissionModule } from '@/types'
import type { PageParams } from './user'

export type CreatePermissionData = {
  code: string
  name: string
  module: PermissionModule
}

export type UpdatePermissionData = {
  name?: string
  module?: PermissionModule
}

/** 权限相关接口 */
export const permissionApi = {
  /** 全量权限（供分配权限 / 权限矩阵使用） */
  listAll(): Promise<Permission[]> {
    return get<Permission[]>('/permissions/')
  },

  /** 分页搜索权限 */
  search(params: PageParams): Promise<PageResult<Permission>> {
    return get<PageResult<Permission>>('/permissions/search', params)
  },

  /** 权限详情 */
  detail(id: number): Promise<Permission> {
    return get<Permission>(`/permissions/${id}`)
  },

  /** 创建权限 */
  create(data: CreatePermissionData): Promise<Permission> {
    return post<Permission>('/permissions', data)
  },

  /** 更新权限（code 不可修改） */
  update(id: number, data: UpdatePermissionData): Promise<Permission> {
    return put<Permission>(`/permissions/${id}`, data)
  },

  /** 删除权限 */
  remove(id: number): Promise<null> {
    return del<null>(`/permissions/${id}`)
  },
}
