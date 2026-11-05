import { randomUUID } from 'node:crypto'
import type { ApiResponse, MockRoute, RouteContext } from '../types'
import { getUserPermissionCodes, publicUser } from '../seed'

const CAPTCHA_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

function genCaptchaText(): string {
  let s = ''
  for (let i = 0; i < 4; i++) s += CAPTCHA_CHARS[Math.floor(Math.random() * CAPTCHA_CHARS.length)]
  return s
}

export const authRoutes: MockRoute[] = [
  {
    method: 'get',
    path: '/api/auth/captcha',
    permission: 'open',
    handler(ctx: RouteContext): ApiResponse<{ captchaId: string; text: string }> {
      const captchaId = randomUUID()
      const text = genCaptchaText()
      ctx.db.captcha.set(captchaId, text)
      return { code: 200, message: 'ok', data: { captchaId, text } }
    },
  },
  {
    method: 'post',
    path: '/api/auth/login',
    permission: 'open',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const { username, password, captchaId, captcha } = ctx.body
      const expected = ctx.db.captcha.get(String(captchaId))
      if (!expected || expected.toLowerCase() !== String(captcha).toLowerCase()) {
        return { code: 400, message: '验证码错误', data: null }
      }
      ctx.db.captcha.delete(String(captchaId))

      const user = ctx.db.users.find((u) => u.username === String(username))
      if (!user || user.password !== String(password)) {
        return { code: 400, message: '用户名或密码错误', data: null }
      }
      if (!user.isActive) {
        return { code: 400, message: '账号已停用', data: null }
      }

      const token = randomUUID()
      ctx.db.sessions.push({ token, userId: user.id })
      return { code: 200, message: '登录成功', data: { token, user: publicUser(user) } }
    },
  },
  {
    method: 'get',
    path: '/api/users/me',
    permission: 'login',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      return { code: 200, message: 'ok', data: publicUser(ctx.user!) }
    },
  },
  {
    method: 'get',
    path: '/api/users/me/permissions',
    permission: 'login',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      return { code: 200, message: 'ok', data: getUserPermissionCodes(ctx.db, ctx.user!) }
    },
  },
]
