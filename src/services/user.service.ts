import { userApi } from '@/apis/user'
import type { PageResult, User } from '@/types'

/** 用户状态到展示文案的映射（业务逻辑示例） */
export const USER_STATUS_LABEL: Record<User['status'], string> = {
  active: '启用',
  disabled: '禁用',
}

/**
 * 用户业务逻辑层：
 * 在 apis 之上封装业务规则，页面只依赖 service，不直接接触 apis。
 */
export const userService = {
  /** 分页查询用户列表，并附加状态展示文案 */
  async list(params: { page?: number; pageSize?: number }): Promise<PageResult<User>> {
    const result = await userApi.list(params)
    return result
  },

  /** 查询用户详情 */
  async detail(id: number): Promise<User> {
    return userApi.detail(id)
  },

  /** 创建用户（业务校验示例：邮箱必填） */
  async create(data: { name: string; email: string; role: string }): Promise<User> {
    if (!data.name.trim()) {
      throw new Error('用户名不能为空')
    }
    if (!data.email.trim()) {
      throw new Error('邮箱不能为空')
    }
    return userApi.create(data)
  },
}
