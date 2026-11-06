import { authApi } from '@/apis/auth'
import type { AuthSession, Captcha, User } from '@/types'

const TOKEN_KEY = 'access_token'

/**
 * 认证业务逻辑层：负责登录前校验、token 存取与当前用户信息查询。
 */
export const authService = {
  /** 获取图形验证码 */
  captcha(): Promise<Captcha> {
    return authApi.captcha()
  },

  /** 登录（校验必填项，成功后持久化 token） */
  async login(data: { username: string; password: string; captchaId: string; captcha: string }): Promise<AuthSession> {
    if (!data.username.trim()) throw new Error('用户名不能为空')
    if (!data.password.trim()) throw new Error('密码不能为空')
    if (!data.captcha.trim()) throw new Error('验证码不能为空')
    const session = await authApi.login(data)
    localStorage.setItem(TOKEN_KEY, session.token)
    return session
  },

  /** 当前用户信息 */
  me(): Promise<User> {
    return authApi.me()
  },

  /** 当前用户权限码 */
  mePermissions(): Promise<string[]> {
    return authApi.mePermissions()
  },

  /** 当前 token */
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  /** 是否已登录 */
  isLoggedIn(): boolean {
    return Boolean(localStorage.getItem(TOKEN_KEY))
  },

  /** 退出登录：清空 token */
  logout(): void {
    localStorage.removeItem(TOKEN_KEY)
  },
}
