import type { MockDb, MockPermission, MockRole, MockUser, PermissionModule } from './types'

const PERMISSION_DEFS: Array<{ code: string; name: string; module: PermissionModule }> = [
  { code: 'user:list', name: '用户列表查看', module: 'user' },
  { code: 'user:read', name: '用户详情查看', module: 'user' },
  { code: 'user:create', name: '创建用户', module: 'user' },
  { code: 'user:update', name: '更新用户', module: 'user' },
  { code: 'user:delete', name: '删除用户', module: 'user' },
  { code: 'user:assign_roles', name: '给用户分配角色', module: 'user' },
  { code: 'user:read_roles', name: '查看用户角色', module: 'user' },
  { code: 'role:list', name: '角色列表查看', module: 'role' },
  { code: 'role:read', name: '角色详情查看', module: 'role' },
  { code: 'role:create', name: '创建角色', module: 'role' },
  { code: 'role:update', name: '更新角色', module: 'role' },
  { code: 'role:delete', name: '删除角色', module: 'role' },
  { code: 'role:assign_permissions', name: '给角色分配权限', module: 'role' },
  { code: 'permission:list', name: '权限列表查看', module: 'permission' },
  { code: 'permission:read', name: '权限详情查看', module: 'permission' },
  { code: 'permission:create', name: '创建权限', module: 'permission' },
  { code: 'permission:update', name: '更新权限', module: 'permission' },
  { code: 'permission:delete', name: '删除权限', module: 'permission' },
  { code: 'system:api_keys', name: 'API 密钥管理', module: 'system' },
  { code: 'system:audit', name: '审计日志查看', module: 'system' },
  { code: 'system:alerts', name: '告警规则管理', module: 'system' },
  { code: 'system:settings', name: '系统配置管理', module: 'system' },
]

export const ALL_PERMISSION_CODES: string[] = PERMISSION_DEFS.map((p) => p.code)

const OPS_ADMIN_CODES = [
  'user:list',
  'user:read',
  'user:create',
  'user:update',
  'user:read_roles',
  'role:list',
  'role:read',
  'role:create',
  'role:update',
  'permission:list',
  'permission:read',
]

const VIEWER_CODES = [
  'user:list',
  'user:read',
  'user:read_roles',
  'role:list',
  'role:read',
  'permission:list',
  'permission:read',
]

const ROLE_DEFS: Array<{
  code: string
  name: string
  description: string
  isSystem: boolean
  permissionCodes: string[]
}> = [
  { code: 'super_admin', name: '超级管理员', description: '拥有平台全部权限，可管理一切资源', isSystem: true, permissionCodes: [...ALL_PERMISSION_CODES] },
  { code: 'ops_admin', name: '运营管理员', description: '负责日常运营，可增改用户与角色，不可删除或分配', isSystem: false, permissionCodes: OPS_ADMIN_CODES },
  { code: 'viewer', name: '只读观察者', description: '只能查看用户、角色与权限，不可做任何修改', isSystem: false, permissionCodes: VIEWER_CODES },
]

const USER_DEFS: Array<{
  username: string
  email: string
  isActive: boolean
  isSuperuser: boolean
  roleCodes: string[]
  createdAt: string
}> = [
  { username: 'admin', email: 'admin@chenguang.ai', isActive: true, isSuperuser: true, roleCodes: ['super_admin'], createdAt: '2026-03-19 10:24' },
  { username: 'ops', email: 'ops@chenguang.ai', isActive: true, isSuperuser: false, roleCodes: ['ops_admin'], createdAt: '2026-03-20 09:11' },
  { username: 'viewer', email: 'viewer@chenguang.ai', isActive: true, isSuperuser: false, roleCodes: ['viewer'], createdAt: '2026-03-21 14:02' },
  { username: 'zhangwei', email: 'zhangwei@chenguang.ai', isActive: true, isSuperuser: false, roleCodes: ['ops_admin'], createdAt: '2026-04-02 16:45' },
  { username: 'liming', email: 'liming@chenguang.ai', isActive: false, isSuperuser: false, roleCodes: ['viewer'], createdAt: '2026-04-10 08:30' },
  { username: 'wangfang', email: 'wangfang@chenguang.ai', isActive: true, isSuperuser: false, roleCodes: ['ops_admin', 'viewer'], createdAt: '2026-05-06 11:20' },
]

/** 构造一份全新的内存种子数据（每次调用互不影响，供测试隔离使用） */
export function createSeed(): MockDb {
  const permissions: MockPermission[] = PERMISSION_DEFS.map((p, i) => ({ id: i + 1, ...p }))
  const roles: MockRole[] = ROLE_DEFS.map((r, i) => ({
    id: i + 1,
    code: r.code,
    name: r.name,
    description: r.description,
    isSystem: r.isSystem,
    permissionCodes: [...r.permissionCodes],
  }))
  const roleIdByCode = new Map(roles.map((r) => [r.code, r.id]))
  const users: MockUser[] = USER_DEFS.map((u, i) => ({
    id: i + 1,
    username: u.username,
    email: u.email,
    password: '123456',
    isActive: u.isActive,
    isSuperuser: u.isSuperuser,
    roleIds: u.roleCodes.map((c) => roleIdByCode.get(c)).filter((x): x is number => x !== undefined),
    createdAt: u.createdAt,
  }))
  return { permissions, roles, users, sessions: [], captcha: new Map() }
}

/** 取用户权限码并集；超管返回全部；结果去重并按字典序排序 */
export function getUserPermissionCodes(db: MockDb, user: MockUser): string[] {
  if (user.isSuperuser) return [...ALL_PERMISSION_CODES].sort()
  const set = new Set<string>()
  for (const roleId of user.roleIds) {
    const role = db.roles.find((r) => r.id === roleId)
    role?.permissionCodes.forEach((c) => set.add(c))
  }
  return [...set].sort()
}

/** 去除敏感字段后的用户公开视图 */
export function publicUser(user: MockUser): Omit<MockUser, 'password'> {
  const { password: _password, ...rest } = user
  return rest
}
