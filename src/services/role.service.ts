import { roleApi, type CreateRoleData, type UpdateRoleData } from '@/apis/role'
import type { PageParams } from '@/apis/user'
import type { PageResult, Role } from '@/types'

/**
 * 角色业务逻辑层：封装角色 CRUD 与权限分配的必填校验。
 */
export const roleService = {
  /** 全量角色 */
  listAll(): Promise<Role[]> {
    return roleApi.listAll()
  },

  /** 分页搜索角色 */
  list(params: PageParams): Promise<PageResult<Role>> {
    return roleApi.search(params)
  },

  /** 角色详情 */
  detail(id: number): Promise<Role> {
    return roleApi.detail(id)
  },

  /** 创建角色（角色码 / 名称必填） */
  async create(data: CreateRoleData): Promise<Role> {
    if (!data.code.trim()) throw new Error('角色码不能为空')
    if (!data.name.trim()) throw new Error('角色名不能为空')
    return roleApi.create(data)
  },

  /** 更新角色（角色码 / 名称不能为空） */
  async update(id: number, data: UpdateRoleData): Promise<Role> {
    if (data.code !== undefined && !data.code.trim()) throw new Error('角色码不能为空')
    if (data.name !== undefined && !data.name.trim()) throw new Error('角色名不能为空')
    return roleApi.update(id, data)
  },

  /** 删除角色 */
  remove(id: number): Promise<null> {
    return roleApi.remove(id)
  },

  /** 给角色分配权限 */
  assignPermissions(id: number, permissionCodes: string[]): Promise<Role> {
    return roleApi.assignPermissions(id, permissionCodes)
  },
}
