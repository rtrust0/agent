import { get, post } from './http'
import { toUser, type BackendUser } from './dto'
import type { AuthSession, User } from '@/types'

interface BackendLoginResponse {
  token: string
  user: BackendUser
}

/** 认证相关接口（对接 FastAPI：/api/v1/auth、/api/v1/users/me） */
export const authApi = {
  /** 登录，返回 token 与当前用户 */
  async login(data: { username: string; password: string }): Promise<AuthSession> {
    const response = await post<BackendLoginResponse>('/auth/login', data)
    return { token: response.token, user: toUser(response.user) }
  },

  /** 当前登录用户信息（含角色） */
  async me(): Promise<User> {
    return toUser(await get<BackendUser>('/users/me'))
  },

  /** 当前登录用户权限码（去重、已排序） */
  mePermissions(): Promise<string[]> {
    return get<string[]>('/users/me/permissions')
  },
}
