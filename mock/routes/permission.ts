import type { ApiResponse, MockPermission, MockRoute, PermissionModule, RouteContext } from '../types'

const MODULES: PermissionModule[] = ['user', 'role', 'permission', 'system']

function findPermission(db: RouteContext['db'], id: string): MockPermission | undefined {
  return db.permissions.find((p) => p.id === Number(id))
}

export const permissionRoutes: MockRoute[] = [
  {
    method: 'get',
    path: '/api/permissions/',
    permission: 'login',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      return { code: 200, message: 'ok', data: ctx.db.permissions }
    },
  },
  {
    method: 'get',
    path: '/api/permissions/search',
    permission: 'permission:list',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const page = Number(ctx.query.get('page') ?? 1)
      const pageSize = Number(ctx.query.get('pageSize') ?? 10)
      const keyword = (ctx.query.get('keyword') ?? '').trim()
      let list = ctx.db.permissions
      if (keyword) {
        list = list.filter((p) => p.code.includes(keyword) || p.name.includes(keyword))
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
    path: '/api/permissions/:id',
    permission: 'permission:read',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const permission = findPermission(ctx.db, ctx.params.id)
      if (!permission) return { code: 404, message: '权限不存在', data: null }
      return { code: 200, message: 'ok', data: permission }
    },
  },
  {
    method: 'post',
    path: '/api/permissions',
    permission: 'permission:create',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const code = String(ctx.body.code ?? '').trim()
      const name = String(ctx.body.name ?? '').trim()
      const module = String(ctx.body.module ?? '') as PermissionModule
      if (!code) return { code: 400, message: '权限码不能为空', data: null }
      if (!name) return { code: 400, message: '权限名不能为空', data: null }
      if (!MODULES.includes(module)) return { code: 400, message: '模块不合法', data: null }
      if (ctx.db.permissions.some((p) => p.code === code)) return { code: 400, message: '权限码已存在', data: null }
      const nextId = Math.max(0, ...ctx.db.permissions.map((p) => p.id)) + 1
      const permission: MockPermission = {
        id: nextId,
        code,
        name,
        module,
        createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      }
      ctx.db.permissions.push(permission)
      return { code: 200, message: '创建成功', data: permission }
    },
  },
  {
    method: 'put',
    path: '/api/permissions/:id',
    permission: 'permission:update',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const permission = findPermission(ctx.db, ctx.params.id)
      if (!permission) return { code: 404, message: '权限不存在', data: null }
      if (ctx.body.code !== undefined && String(ctx.body.code) !== permission.code) {
        return { code: 400, message: '权限码不可修改', data: null }
      }
      if (ctx.body.name !== undefined) permission.name = String(ctx.body.name).trim()
      if (ctx.body.module !== undefined) {
        const module = String(ctx.body.module) as PermissionModule
        if (!MODULES.includes(module)) return { code: 400, message: '模块不合法', data: null }
        permission.module = module
      }
      return { code: 200, message: '更新成功', data: permission }
    },
  },
  {
    method: 'delete',
    path: '/api/permissions/:id',
    permission: 'permission:delete',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      const permission = findPermission(ctx.db, ctx.params.id)
      if (!permission) return { code: 404, message: '权限不存在', data: null }
      if (ctx.db.roles.some((r) => r.permissionCodes.includes(permission.code))) {
        return { code: 400, message: '权限已被角色引用，不可删除', data: null }
      }
      ctx.db.permissions.splice(ctx.db.permissions.indexOf(permission), 1)
      return { code: 200, message: '删除成功', data: null }
    },
  },
]
