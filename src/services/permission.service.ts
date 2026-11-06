import {
  permissionApi,
  type CreatePermissionData,
  type UpdatePermissionData,
} from '@/apis/permission'
import type { PageParams } from '@/apis/user'
import type { PageResult, Permission } from '@/types'

/**
 * 权限业务逻辑层：封装权限 CRUD 的必填校验。
 */
export const permissionService = {
  /** 全量权限 */
  listAll(): Promise<Permission[]> {
    return permissionApi.listAll()
  },

  /** 分页搜索权限 */
  list(params: PageParams): Promise<PageResult<Permission>> {
    return permissionApi.search(params)
  },

  /** 权限详情 */
  detail(id: number): Promise<Permission> {
    return permissionApi.detail(id)
  },

  /** 创建权限（权限码 / 名称 / 模块必填） */
  async create(data: CreatePermissionData): Promise<Permission> {
    if (!data.code.trim()) throw new Error('权限码不能为空')
    if (!data.name.trim()) throw new Error('权限名不能为空')
    if (!data.module) throw new Error('模块不能为空')
    return permissionApi.create(data)
  },

  /** 更新权限 */
  update(id: number, data: UpdatePermissionData): Promise<Permission> {
    return permissionApi.update(id, data)
  },

  /** 删除权限 */
  remove(id: number): Promise<null> {
    return permissionApi.remove(id)
  },
}
