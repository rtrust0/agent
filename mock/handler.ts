import type { IncomingMessage, ServerResponse } from 'node:http'
import type { ApiResponse, MockDb, MockRequestHandler, MockRoute, RouteContext } from './types'
import { createSeed, getUserPermissionCodes } from './seed'
import { authRoutes } from './routes/auth'
import { userRoutes } from './routes/user'

const allRoutes: MockRoute[] = [...authRoutes, ...userRoutes]

function readBody(req: IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve) => {
    let raw = ''
    req.on('data', (chunk) => {
      raw += chunk
    })
    req.on('end', () => {
      if (!raw.trim()) return resolve({})
      try {
        resolve(JSON.parse(raw))
      } catch {
        resolve({})
      }
    })
  })
}

function matchPath(pattern: string, pathname: string): Record<string, string> | null {
  const pp = pattern.split('/')
  const up = pathname.split('/')
  if (pp.length !== up.length) return null
  const params: Record<string, string> = {}
  for (let i = 0; i < pp.length; i++) {
    const p = pp[i]
    const u = up[i]
    if (p.startsWith(':')) params[p.slice(1)] = decodeURIComponent(u)
    else if (p !== u) return null
  }
  return params
}

function extractToken(authorization?: string): string | undefined {
  if (!authorization) return undefined
  const m = authorization.match(/^Bearer\s+(.+)$/i)
  return m ? m[1] : undefined
}

/**
 * 构建可独立测试的 mock 请求处理器：解析 URL/方法/body/鉴权，做路由匹配
 * 与三级权限拦截（open / login / 权限码），未命中返回 404。HTTP 状态码恒为
 * 200，业务结果通过响应体 `code` 字段表达。
 */
export function createMockHandler(seed?: MockDb): MockRequestHandler {
  const db = seed ?? createSeed()
  return async (req, res) => {
    const url = new URL(req.url ?? '/', 'http://localhost')
    const method = (req.method ?? 'get').toLowerCase()

    const respond = (payload: ApiResponse<unknown>) => {
      res.statusCode = 200
      res.setHeader('Content-Type', 'application/json; charset=utf-8')
      res.end(JSON.stringify(payload))
    }

    let matched: { route: MockRoute; params: Record<string, string> } | null = null
    for (const route of allRoutes) {
      if (route.method !== method) continue
      const params = matchPath(route.path, url.pathname)
      if (params) {
        matched = { route, params }
        break
      }
    }

    if (!matched) {
      return respond({ code: 404, message: '接口不存在', data: null })
    }

    const { route, params } = matched
    const body = await readBody(req)

    const token = extractToken(req.headers.authorization)
    let user: MockDb['users'][number] | undefined
    if (token) {
      const session = db.sessions.find((s) => s.token === token)
      if (session) user = db.users.find((u) => u.id === session.userId)
    }

    if (route.permission !== 'open') {
      if (!user) return respond({ code: 401, message: '未登录或登录已过期', data: null })
      if (route.permission !== 'login' && !user.isSuperuser && !getUserPermissionCodes(db, user).includes(route.permission)) {
        return respond({ code: 403, message: '没有权限执行该操作', data: null })
      }
    }

    const ctx: RouteContext = { db, user, body, query: url.searchParams, params }
    respond(route.handler(ctx))
  }
}
