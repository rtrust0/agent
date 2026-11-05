import type { ApiResponse, MockRole, MockRoute, MockUser, RouteContext } from '../types'
import { publicUser } from '../seed'

function findUser(db: RouteContext['db'], id: string): MockUser | undefined {
  return db.users.find((u) => u.id === Number(id))
}

export const userRoutes: MockRoute[] = [
  {
    method: 'get',
    path: '/api/users',
    permission: 'login',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      return { code: 200, message: 'ok', data: ctx.db.users.map(publicUser) }
    },
  },
  {
    method: 'get',
    path: '/api/users/search',
    permission: 'user:list',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const page = Number(ctx.query.get('page') ?? 1)
      const pageSize = Number(ctx.query.get('pageSize') ?? 10)
      const keyword = (ctx.query.get('keyword') ?? '').trim()
      let list = ctx.db.users
      if (keyword) {
        list = list.filter((u) => u.username.includes(keyword) || u.email.includes(keyword))
      }
      const start = (page - 1) * pageSize
      return {
        code: 200,
        message: 'ok',
        data: {
          list: list.slice(start, start + pageSize).map(publicUser),
          total: list.length,
          page,
          pageSize,
        },
      }
    },
  },
  {
    method: 'get',
    path: '/api/users/:id',
    permission: 'user:read',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const user = findUser(ctx.db, ctx.params.id)
      if (!user) return { code: 404, message: '用户不存在', data: null }
      return { code: 200, message: 'ok', data: publicUser(user) }
    },
  },
  {
    method: 'post',
    path: '/api/users',
    permission: 'user:create',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const username = String(ctx.body.username ?? '').trim()
      const email = String(ctx.body.email ?? '').trim()
      const password = String(ctx.body.password ?? '')
      if (!username) return { code: 400, message: '用户名不能为空', data: null }
      if (!email) return { code: 400, message: '邮箱不能为空', data: null }
      if (!password) return { code: 400, message: '密码不能为空', data: null }
      if (ctx.db.users.some((u) => u.username === username)) {
        return { code: 400, message: '用户名已存在', data: null }
      }
      const roleIds = Array.isArray(ctx.body.roleIds)
        ? (ctx.body.roleIds as unknown[]).map(Number).filter((id) => ctx.db.roles.some((r) => r.id === id))
        : []
      const nextId = Math.max(0, ...ctx.db.users.map((u) => u.id)) + 1
      const user: MockUser = {
        id: nextId,
        username,
        email,
        password,
        isActive: ctx.body.isActive === undefined ? true : Boolean(ctx.body.isActive),
        isSuperuser: false,
        roleIds,
        createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      }
      ctx.db.users.push(user)
      return { code: 200, message: '创建成功', data: publicUser(user) }
    },
  },
  {
    method: 'delete',
    path: '/api/users/:id',
    permission: 'user:delete',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const idx = ctx.db.users.findIndex((u) => u.id === Number(ctx.params.id))
      if (idx === -1) return { code: 404, message: '用户不存在', data: null }
      ctx.db.users.splice(idx, 1)
      return { code: 200, message: '删除成功', data: null }
    },
  },
  {
    method: 'put',
    path: '/api/users/:id/roles',
    permission: 'user:assign_roles',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const user = findUser(ctx.db, ctx.params.id)
      if (!user) return { code: 404, message: '用户不存在', data: null }
      const roleIds = Array.isArray(ctx.body.roleIds)
        ? (ctx.body.roleIds as unknown[]).map(Number).filter((id) => ctx.db.roles.some((r) => r.id === id))
        : []
      user.roleIds = roleIds
      return { code: 200, message: '分配成功', data: publicUser(user) }
    },
  },
  {
    method: 'get',
    path: '/api/users/:id/roles',
    permission: 'user:read_roles',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const user = findUser(ctx.db, ctx.params.id)
      if (!user) return { code: 404, message: '用户不存在', data: null }
      const roles = user.roleIds
        .map((id) => ctx.db.roles.find((r) => r.id === id))
        .filter((r): r is MockRole => r !== undefined)
      return { code: 200, message: 'ok', data: roles }
    },
  },
]
