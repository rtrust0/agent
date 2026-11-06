import { del, get, post, put } from './http'
import type { PageResult, Role, User } from '@/types'

export type PageParams = { page?: number; pageSize?: number; keyword?: string }

export type CreateUserData = {
  username: string
  email: string
  password: string
  roleIds?: number[]
  isActive?: boolean
}

/** 用户相关接口 */
export const userApi = {
  /** 全量用户（供分配角色弹窗） */
  listAll(): Promise<User[]> {
    return get<User[]>('/users')
  },

  /** 分页搜索用户 */
  search(params: PageParams): Promise<PageResult<User>> {
    return get<PageResult<User>>('/users/search', params)
  },

  /** 用户详情 */
  detail(id: number): Promise<User> {
    return get<User>(`/users/${id}`)
  },

  /** 创建用户 */
  create(data: CreateUserData): Promise<User> {
    return post<User>('/users', data)
  },

  /** 删除用户 */
  remove(id: number): Promise<null> {
    return del<null>(`/users/${id}`)
  },

  /** 给用户分配角色 */
  assignRoles(id: number, roleIds: number[]): Promise<User> {
    return put<User>(`/users/${id}/roles`, { roleIds })
  },

  /** 查看用户角色 */
  readRoles(id: number): Promise<Role[]> {
    return get<Role[]>(`/users/${id}/roles`)
  },
}
