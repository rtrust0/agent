import type { ApiResponse, MockRoute, RouteContext } from '../types'

export const dashboardRoutes: MockRoute[] = [
  {
    method: 'get',
    path: '/api/dashboard/summary',
    permission: 'login',
    handler(ctx: RouteContext): ApiResponse<unknown> {
      return {
        code: 200,
        message: 'ok',
        data: {
          totalUsers: ctx.db.users.length,
          totalRoles: ctx.db.roles.length,
          totalPermissions: ctx.db.permissions.length,
        },
      }
    },
  },
]
