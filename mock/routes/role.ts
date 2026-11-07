import type { ApiResponse, MockRole, MockRoute, RouteContext } from '../types'

function findRole(db: RouteContext['db'], id: string): MockRole | undefined {
  return db.roles.find((r) => r.id === Number(id))
}

function validPermissionCodes(db: RouteContext['db'], codes: unknown): string[] {
  if (!Array.isArray(codes)) return []
  return (codes as unknown[]).map(String).filter((c) => db.permissions.some((p) => p.code === c))
}

export const roleRoutes: MockRoute[] = [
  {
    method: 'get',
    path: '/api/roles/',
    permission: 'login',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      return { code: 200, message: 'ok', data: ctx.db.roles }
    },
  },
  {
    method: 'get',
    path: '/api/roles/search',
    permission: 'role:list',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const page = Number(ctx.query.get('page') ?? 1)
      const pageSize = Number(ctx.query.get('pageSize') ?? 10)
      const keyword = (ctx.query.get('keyword') ?? '').trim()
      let list = ctx.db.roles
      if (keyword) {
        list = list.filter((r) => r.code.includes(keyword) || r.name.includes(keyword))
      }
      const start = (page - 1) * pageSize
      return {
        code: 200,
        message: 'ok',
        data: { list: list.slice(start, start + pageSize), total: list.length, page, pageSize },
      }
    },
  },
  {
    method: 'get',
    path: '/api/roles/:id',
    permission: 'role:read',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const role = findRole(ctx.db, ctx.params.id)
      if (!role) return { code: 404, message: '角色不存在', data: null }
      return { code: 200, message: 'ok', data: role }
    },
  },
  {
    method: 'post',
    path: '/api/roles',
    permission: 'role:create',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const code = String(ctx.body.code ?? '').trim()
      const name = String(ctx.body.name ?? '').trim()
      if (!code) return { code: 400, message: '角色码不能为空', data: null }
      if (!name) return { code: 400, message: '角色名不能为空', data: null }
      if (ctx.db.roles.some((r) => r.code === code)) return { code: 400, message: '角色码已存在', data: null }
      const nextId = Math.max(0, ...ctx.db.roles.map((r) => r.id)) + 1
      const role: MockRole = {
        id: nextId,
        code,
        name,
        description: String(ctx.body.description ?? ''),
        isSystem: false,
        permissionCodes: validPermissionCodes(ctx.db, ctx.body.permissionCodes),
        createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      }
      ctx.db.roles.push(role)
      return { code: 200, message: '创建成功', data: role }
    },
  },
  {
    method: 'put',
    path: '/api/roles/:id',
    permission: 'role:update',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const role = findRole(ctx.db, ctx.params.id)
      if (!role) return { code: 404, message: '角色不存在', data: null }
      if (role.isSystem) return { code: 400, message: '内置角色不可修改', data: null }
      if (ctx.body.code !== undefined) {
        const code = String(ctx.body.code).trim()
        if (!code) return { code: 400, message: '角色码不能为空', data: null }
        if (ctx.db.roles.some((r) => r.id !== role.id && r.code === code)) {
          return { code: 400, message: '角色码已存在', data: null }
        }
        role.code = code
      }
      if (ctx.body.name !== undefined) {
        const name = String(ctx.body.name).trim()
        if (!name) return { code: 400, message: '角色名不能为空', data: null }
        role.name = name
      }
      if (ctx.body.description !== undefined) role.description = String(ctx.body.description)
      return { code: 200, message: '更新成功', data: role }
    },
  },
  {
    method: 'delete',
    path: '/api/roles/:id',
    permission: 'role:delete',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const role = findRole(ctx.db, ctx.params.id)
      if (!role) return { code: 404, message: '角色不存在', data: null }
      if (role.isSystem) return { code: 400, message: '内置角色不可删除', data: null }
      ctx.db.roles.splice(ctx.db.roles.indexOf(role), 1)
      return { code: 200, message: '删除成功', data: null }
    },
  },
  {
    method: 'put',
    path: '/api/roles/:id/permissions',
    permission: 'role:assign_permissions',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const role = findRole(ctx.db, ctx.params.id)
      if (!role) return { code: 404, message: '角色不存在', data: null }
      if (role.isSystem) return { code: 400, message: '内置角色不可修改权限', data: null }
      role.permissionCodes = validPermissionCodes(ctx.db, ctx.body.permissionCodes)
      return { code: 200, message: '分配成功', data: role }
    },
  },
]
