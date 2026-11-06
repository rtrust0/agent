import type { IncomingMessage, ServerResponse } from 'node:http'

export type PermissionModule = 'user' | 'role' | 'permission' | 'system'

export interface MockPermission {
  id: number
  code: string
  name: string
  module: PermissionModule
  createdAt: string
}

export interface MockRole {
  id: number
  code: string
  name: string
  description: string
  isSystem: boolean
  permissionCodes: string[]
  createdAt: string
}

export interface MockUser {
  id: number
  username: string
  email: string
  password: string
  isActive: boolean
  isSuperuser: boolean
  roleIds: number[]
  createdAt: string
}

export interface MockSession {
  token: string
  userId: number
}

export interface MockDb {
  permissions: MockPermission[]
  roles: MockRole[]
  users: MockUser[]
  sessions: MockSession[]
  captcha: Map<string, string>
}

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface RouteContext {
  db: MockDb
  user?: MockUser
  body: Record<string, unknown>
  query: URLSearchParams
  params: Record<string, string>
}

export type MockRouteHandler = (ctx: RouteContext) => ApiResponse<unknown>

export interface MockRoute {
  method: 'get' | 'post' | 'put' | 'delete'
  path: string
  /** 'open' = 无需登录；'login' = 需登录无权限码；其余为具体权限码 */
  permission: 'open' | 'login' | string
  handler: MockRouteHandler
}

export type MockRequestHandler = (req: IncomingMessage, res: ServerResponse) => Promise<void>
