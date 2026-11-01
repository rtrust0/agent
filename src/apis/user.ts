import { get, post } from './http'
import type { PageResult, User } from '@/types'

/** 用户相关接口 */
export const userApi = {
  /** 分页查询用户列表 */
  list(params: { page?: number; pageSize?: number }): Promise<PageResult<User>> {
    return get<PageResult<User>>('/user/list', params)
  },

  /** 查询用户详情 */
  detail(id: number): Promise<User> {
    return get<User>('/user/detail', { id })
  },

  /** 创建用户 */
  create(data: { name: string; email: string; role: string }): Promise<User> {
    return post<User>('/user/create', data)
  },
}
