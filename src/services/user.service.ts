import { userApi, type CreateUserData, type PageParams } from '@/apis/user'
import type { PageResult, Role, User } from '@/types'

/**
 * 用户业务逻辑层：
 * 在 apis 之上封装业务规则，页面只依赖 service，不直接接触 apis。
 */
export const userService = {
  /** 全量用户（分配角色弹窗） */
  listAll(): Promise<User[]> {
    return userApi.listAll()
  },

  /** 分页搜索用户 */
  list(params: PageParams): Promise<PageResult<User>> {
    return userApi.search(params)
  },

  /** 用户详情 */
  detail(id: number): Promise<User> {
    return userApi.detail(id)
  },

  /** 创建用户（业务校验：用户名 / 邮箱 / 密码必填） */
  async create(data: CreateUserData): Promise<User> {
    if (!data.username.trim()) throw new Error('用户名不能为空')
    if (!data.email.trim()) throw new Error('邮箱不能为空')
    if (!data.password.trim()) throw new Error('密码不能为空')
    return userApi.create(data)
  },

  /** 删除用户 */
  remove(id: number): Promise<null> {
    return userApi.remove(id)
  },

  /** 给用户分配角色 */
  assignRoles(id: number, roleIds: number[]): Promise<User> {
    return userApi.assignRoles(id, roleIds)
  },

  /** 查看用户角色 */
  readRoles(id: number): Promise<Role[]> {
    return userApi.readRoles(id)
  },
}
