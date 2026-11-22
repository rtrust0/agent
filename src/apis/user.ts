import { del, get, post, put } from './http'
import {
  toPage,
  toRole,
  toUser,
  type BackendPage,
  type BackendRole,
  type BackendRoleBrief,
  type BackendUser,
} from './dto'
import type { PageResult, Role, User } from '@/types'

export type PageParams = { page?: number; pageSize?: number; keyword?: string }

export type CreateUserData = {
  username: string
  email: string
  password: string
  roleIds?: number[]
  isActive?: boolean
}

/** 将前端分页参数转换为后端命名 */
export function toPageQuery(params: PageParams): Record<string, unknown> {
  return {
    page: params.page ?? 1,
    page_size: params.pageSize ?? 10,
    keyword: params.keyword || undefined,
  }
}

/** 用户相关接口（对接 FastAPI：/api/v1/users） */
export const userApi = {
  /** 全量用户（供分配角色弹窗） */
  async listAll(): Promise<User[]> {
    const users = await get<BackendUser[]>('/users')
    return users.map(toUser)
  },

  /** 分页搜索用户 */
  async search(params: PageParams): Promise<PageResult<User>> {
    const page = await get<BackendPage<BackendUser>>('/users/search', toPageQuery(params))
    return toPage(page, toUser)
  },

  /** 用户详情 */
  async detail(id: number): Promise<User> {
    return toUser(await get<BackendUser>(`/users/${id}`))
  },

  /** 创建用户 */
  async create(data: CreateUserData): Promise<User> {
    const created = await post<BackendUser>('/users', {
      username: data.username,
      email: data.email,
      password: data.password,
      role_ids: data.roleIds ?? [],
      is_active: data.isActive ?? true,
    })
    return toUser(created)
  },

  /** 删除用户 */
  remove(id: number): Promise<null> {
    return del<null>(`/users/${id}`)
  },

  /** 给用户分配角色 */
  async assignRoles(id: number, roleIds: number[]): Promise<User> {
    const updated = await put<BackendUser>(`/users/${id}/roles`, { role_ids: roleIds })
    return toUser(updated)
  },

  /** 查看用户角色（后端返回精简角色，这里补齐权限码） */
  async readRoles(id: number): Promise<Role[]> {
    const briefs = await get<BackendRoleBrief[]>(`/users/${id}/roles`)
    const details = await Promise.all(
      briefs.map((brief) => get<BackendRole>(`/roles/${brief.id}`)),
    )
    return details.map(toRole)
  },
}
