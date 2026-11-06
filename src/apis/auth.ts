import { get, post } from './http'
import type { AuthSession, Captcha, User } from '@/types'

/** 认证相关接口 */
export const authApi = {
  /** 获取图形验证码 */
  captcha(): Promise<Captcha> {
    return get<Captcha>('/auth/captcha')
  },

  /** 登录，返回 token 与当前用户 */
  login(data: { username: string; password: string; captchaId: string; captcha: string }): Promise<AuthSession> {
    return post<AuthSession>('/auth/login', data)
  },

  /** 当前登录用户信息 */
  me(): Promise<User> {
    return get<User>('/users/me')
  },

  /** 当前登录用户权限码（去重、已排序） */
  mePermissions(): Promise<string[]> {
    return get<string[]>('/users/me/permissions')
  },
}
