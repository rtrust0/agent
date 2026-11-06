import { del, get, post, put } from './http'
import type { PageResult, Role } from '@/types'
import type { PageParams } from './user'

export type CreateRoleData = {
  code: string
  name: string
  description?: string
  permissionCodes?: string[]
}

export type UpdateRoleData = {
  code?: string
  name?: string
  description?: string
}

/** 角色相关接口 */
export const roleApi = {
  /** 全量角色（供分配角色 / 权限矩阵使用） */
  listAll(): Promise<Role[]> {
    return get<Role[]>('/roles/')
  },

  /** 分页搜索角色 */
  search(params: PageParams): Promise<PageResult<Role>> {
    return get<PageResult<Role>>('/roles/search', params)
  },

  /** 角色详情 */
  detail(id: number): Promise<Role> {
    return get<Role>(`/roles/${id}`)
  },

  /** 创建角色 */
  create(data: CreateRoleData): Promise<Role> {
    return post<Role>('/roles', data)
  },

  /** 更新角色 */
  update(id: number, data: UpdateRoleData): Promise<Role> {
    return put<Role>(`/roles/${id}`, data)
  },

  /** 删除角色 */
  remove(id: number): Promise<null> {
    return del<null>(`/roles/${id}`)
  },

  /** 给角色分配权限 */
  assignPermissions(id: number, permissionCodes: string[]): Promise<Role> {
    return put<Role>(`/roles/${id}/permissions`, { permissionCodes })
  },
}
