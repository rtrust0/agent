import { test } from 'node:test'
import assert from 'node:assert/strict'
import { startMockServer } from './_helpers.ts'
import { createSeed } from '../../mock/index'

const ALL_CODES_SORTED = [
  'permission:create',
  'permission:delete',
  'permission:list',
  'permission:read',
  'permission:update',
  'role:assign_permissions',
  'role:create',
  'role:delete',
  'role:list',
  'role:read',
  'role:update',
  'system:alerts',
  'system:api_keys',
  'system:audit',
  'system:settings',
  'user:assign_roles',
  'user:create',
  'user:delete',
  'user:list',
  'user:read',
  'user:read_roles',
  'user:update',
]

const VIEWER_CODES_SORTED = [
  'permission:list',
  'permission:read',
  'role:list',
  'role:read',
  'user:list',
  'user:read',
  'user:read_roles',
]

interface Api {
  code: number
  message: string
  data: unknown
}

async function api(
  baseUrl: string,
  method: string,
  path: string,
  opts: { token?: string; body?: unknown } = {},
): Promise<Api> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'
  const res = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })
  return res.json() as Promise<Api>
}

async function login(baseUrl: string, username: string, password = '123456') {
  const captcha = await api(baseUrl, 'GET', '/api/auth/captcha')
  const captchaData = captcha.data as { captchaId: string; text: string }
  const res = await api(baseUrl, 'POST', '/api/auth/login', {
    body: { username, password, captchaId: captchaData.captchaId, captcha: captchaData.text },
  })
  assert.equal(res.code, 200, `login ${username}: ${res.message}`)
  return res.data as { token: string; user: { username: string } }
}

async function withServer<T>(fn: (baseUrl: string) => Promise<T>, seed = createSeed()): Promise<T> {
  const srv = await startMockServer(seed)
  try {
    return await fn(srv.baseUrl)
  } finally {
    await srv.close()
  }
}

/** 没有任何角色 / 权限的已登录用户，用于验证 403 */
function rolelessSeed() {
  const seed = createSeed()
  seed.users.push({
    id: 99,
    username: 'nobody',
    email: 'nobody@x.com',
    password: '123456',
    isActive: true,
    isSuperuser: false,
    roleIds: [],
    createdAt: '2026-01-01 00:00',
  })
  return seed
}

// ==================== 认证 ====================

test('captcha returns id and text', () =>
  withServer(async (baseUrl) => {
    const res = await api(baseUrl, 'GET', '/api/auth/captcha')
    assert.equal(res.code, 200)
    const data = res.data as { captchaId: string; text: string }
    assert.ok(data.captchaId)
    assert.match(data.text, /^[A-Z0-9]{4}$/)
  }))

test('login success', () =>
  withServer(async (baseUrl) => {
    const { token, user } = await login(baseUrl, 'admin')
    assert.ok(token)
    assert.equal(user.username, 'admin')
  }))

test('login wrong captcha', () =>
  withServer(async (baseUrl) => {
    const captcha = await api(baseUrl, 'GET', '/api/auth/captcha')
    const captchaData = captcha.data as { captchaId: string }
    const res = await api(baseUrl, 'POST', '/api/auth/login', {
      body: { username: 'admin', password: '123456', captchaId: captchaData.captchaId, captcha: 'XXXX' },
    })
    assert.equal(res.code, 400)
  }))

test('login wrong password', () =>
  withServer(async (baseUrl) => {
    const captcha = await api(baseUrl, 'GET', '/api/auth/captcha')
    const captchaData = captcha.data as { captchaId: string; text: string }
    const res = await api(baseUrl, 'POST', '/api/auth/login', {
      body: { username: 'admin', password: 'bad', captchaId: captchaData.captchaId, captcha: captchaData.text },
    })
    assert.equal(res.code, 400)
  }))

test('login disabled account', () =>
  withServer(async (baseUrl) => {
    const captcha = await api(baseUrl, 'GET', '/api/auth/captcha')
    const captchaData = captcha.data as { captchaId: string; text: string }
    const res = await api(baseUrl, 'POST', '/api/auth/login', {
      body: { username: 'liming', password: '123456', captchaId: captchaData.captchaId, captcha: captchaData.text },
    })
    assert.equal(res.code, 400)
    assert.match(res.message, /停用/)
  }))

test('me requires login', () =>
  withServer(async (baseUrl) => {
    const res = await api(baseUrl, 'GET', '/api/users/me')
    assert.equal(res.code, 401)
  }))

test('me returns current user', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/me', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as { username: string }).username, 'admin')
  }))

test('invalid token is rejected', () =>
  withServer(async (baseUrl) => {
    const res = await api(baseUrl, 'GET', '/api/users/me', { token: 'not-a-real-token' })
    assert.equal(res.code, 401)
  }))

test('me permissions superuser dedup sorted', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/me/permissions', { token })
    assert.equal(res.code, 200)
    assert.deepEqual(res.data, ALL_CODES_SORTED)
  }))

test('me permissions viewer exact list', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'GET', '/api/users/me/permissions', { token })
    assert.equal(res.code, 200)
    assert.deepEqual(res.data, VIEWER_CODES_SORTED)
  }))

// ==================== 用户 ====================

test('users list requires login', () =>
  withServer(async (baseUrl) => {
    const noToken = await api(baseUrl, 'GET', '/api/users')
    assert.equal(noToken.code, 401)

    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as unknown[]).length, 6)
  }))

test('users list login only, no permission required', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/users', { token })
    assert.equal(res.code, 200)
  }, rolelessSeed()))

test('users search pagination', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/search?page=1&pageSize=2', { token })
    assert.equal(res.code, 200)
    const data = res.data as { list: unknown[]; total: number }
    assert.equal(data.total, 6)
    assert.equal(data.list.length, 2)
  }))

test('users search keyword', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/search?keyword=admin', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as { total: number }).total, 1)
  }))

test('users search forbidden without user:list', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/users/search', { token })
    assert.equal(res.code, 403)
  }, rolelessSeed()))

test('user detail success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/1', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as { username: string }).username, 'admin')
  }))

test('user detail 404', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/999', { token })
    assert.equal(res.code, 404)
  }))

test('user detail forbidden without user:read', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/users/1', { token })
    assert.equal(res.code, 403)
  }, rolelessSeed()))

test('user create validation', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/users', { token, body: { email: 'x@x.com', password: '123456' } })
    assert.equal(res.code, 400)
  }))

test('user create duplicate username', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/users', {
      token,
      body: { username: 'admin', email: 'dup@x.com', password: '123456' },
    })
    assert.equal(res.code, 400)
  }))

test('user create success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/users', {
      token,
      body: { username: 'newuser', email: 'new@x.com', password: '123456', roleIds: [3] },
    })
    assert.equal(res.code, 200)
    assert.equal((res.data as { username: string }).username, 'newuser')

    const list = await api(baseUrl, 'GET', '/api/users/search?page=1&pageSize=20', { token })
    assert.equal((list.data as { total: number }).total, 7)
  }))

test('user create forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'POST', '/api/users', {
      token,
      body: { username: 'x', email: 'x@x.com', password: '123456' },
    })
    assert.equal(res.code, 403)
  }))

test('user delete success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'DELETE', '/api/users/6', { token })
    assert.equal(res.code, 200)

    const list = await api(baseUrl, 'GET', '/api/users', { token })
    assert.equal((list.data as unknown[]).length, 5)
  }))

test('user delete 404', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'DELETE', '/api/users/999', { token })
    assert.equal(res.code, 404)
  }))

test('user delete forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'DELETE', '/api/users/1', { token })
    assert.equal(res.code, 403)
  }))

test('user assign roles permission', () =>
  withServer(async (baseUrl) => {
    const viewer = await login(baseUrl, 'viewer')
    const denied = await api(baseUrl, 'PUT', '/api/users/1/roles', { token: viewer.token, body: { roleIds: [3] } })
    assert.equal(denied.code, 403)

    const admin = await login(baseUrl, 'admin')
    const ok = await api(baseUrl, 'PUT', '/api/users/1/roles', { token: admin.token, body: { roleIds: [3] } })
    assert.equal(ok.code, 200)
  }))

test('user read roles empty', () =>
  withServer(async (baseUrl) => {
    const admin = await login(baseUrl, 'admin')
    const created = await api(baseUrl, 'POST', '/api/users', {
      token: admin.token,
      body: { username: 'norole', email: 'norole@x.com', password: '123456', roleIds: [] },
    })
    const id = (created.data as { id: number }).id

    const res = await api(baseUrl, 'GET', `/api/users/${id}/roles`, { token: admin.token })
    assert.equal(res.code, 200)
    assert.deepEqual(res.data, [])
  }))

test('user read roles non-empty', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/1/roles', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as unknown[]).length, 1)
  }))

// ==================== 角色 ====================

test('roles list requires login', () =>
  withServer(async (baseUrl) => {
    assert.equal((await api(baseUrl, 'GET', '/api/roles/')).code, 401)
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/roles/', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as unknown[]).length, 3)
  }))

test('roles list login only, no permission required', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/roles/', { token })
    assert.equal(res.code, 200)
  }, rolelessSeed()))

test('roles search pagination and keyword', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const page = await api(baseUrl, 'GET', '/api/roles/search?page=1&pageSize=2', { token })
    assert.equal(page.code, 200)
    assert.equal((page.data as { list: unknown[] }).list.length, 2)

    const keyword = await api(baseUrl, 'GET', '/api/roles/search?keyword=viewer', { token })
    assert.equal((keyword.data as { total: number }).total, 1)
  }))

test('roles search forbidden without role:list', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/roles/search', { token })
    assert.equal(res.code, 403)
  }, rolelessSeed()))

test('role detail success and 404', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const ok = await api(baseUrl, 'GET', '/api/roles/1', { token })
    assert.equal(ok.code, 200)
    assert.equal((ok.data as { code: string }).code, 'super_admin')

    const missing = await api(baseUrl, 'GET', '/api/roles/999', { token })
    assert.equal(missing.code, 404)
  }))

test('role detail forbidden without role:read', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/roles/1', { token })
    assert.equal(res.code, 403)
  }, rolelessSeed()))

test('role create success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/roles', {
      token,
      body: { code: 'auditor', name: '审计员', description: '审计', permissionCodes: ['user:list'] },
    })
    assert.equal(res.code, 200)
    assert.equal((res.data as { code: string }).code, 'auditor')
  }))

test('role create validation', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/roles', { token, body: { name: '缺码' } })
    assert.equal(res.code, 400)
  }))

test('role create duplicate code', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/roles', { token, body: { code: 'viewer', name: '重复' } })
    assert.equal(res.code, 400)
  }))

test('role create forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'POST', '/api/roles', { token, body: { code: 'x', name: 'x' } })
    assert.equal(res.code, 403)
  }))

test('role update success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'PUT', '/api/roles/3', { token, body: { name: '只读观察员' } })
    assert.equal(res.code, 200)
    assert.equal((res.data as { name: string }).name, '只读观察员')
  }))

test('role update system role forbidden', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'PUT', '/api/roles/1', { token, body: { name: '改名' } })
    assert.equal(res.code, 400)
  }))

test('role update forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'PUT', '/api/roles/3', { token, body: { name: 'x' } })
    assert.equal(res.code, 403)
  }))

test('role delete non-system success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const created = await api(baseUrl, 'POST', '/api/roles', { token, body: { code: 'temp', name: '临时' } })
    const id = (created.data as { id: number }).id
    const res = await api(baseUrl, 'DELETE', `/api/roles/${id}`, { token })
    assert.equal(res.code, 200)

    const list = await api(baseUrl, 'GET', '/api/roles/', { token })
    assert.equal((list.data as unknown[]).length, 3)
  }))

test('role delete system forbidden', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'DELETE', '/api/roles/1', { token })
    assert.equal(res.code, 400)
  }))

test('role delete 404', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'DELETE', '/api/roles/999', { token })
    assert.equal(res.code, 404)
  }))

test('role delete forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'DELETE', '/api/roles/2', { token })
    assert.equal(res.code, 403)
  }))

test('role assign permissions permission', () =>
  withServer(async (baseUrl) => {
    const ops = await login(baseUrl, 'ops')
    const denied = await api(baseUrl, 'PUT', '/api/roles/3/permissions', {
      token: ops.token,
      body: { permissionCodes: ['user:list'] },
    })
    assert.equal(denied.code, 403)

    const admin = await login(baseUrl, 'admin')
    const ok = await api(baseUrl, 'PUT', '/api/roles/3/permissions', {
      token: admin.token,
      body: { permissionCodes: ['user:list', 'role:list'] },
    })
    assert.equal(ok.code, 200)
    assert.deepEqual((ok.data as { permissionCodes: string[] }).permissionCodes, ['user:list', 'role:list'])
  }))

test('role assign permissions system role forbidden', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'PUT', '/api/roles/1/permissions', {
      token,
      body: { permissionCodes: ['user:list'] },
    })
    assert.equal(res.code, 400)
  }))

// ==================== 权限 ====================

test('permissions list requires login', () =>
  withServer(async (baseUrl) => {
    assert.equal((await api(baseUrl, 'GET', '/api/permissions/')).code, 401)
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/permissions/', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as unknown[]).length, 22)
  }))

test('permissions list login only, no permission required', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/permissions/', { token })
    assert.equal(res.code, 200)
  }, rolelessSeed()))

test('permissions search pagination', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/permissions/search?page=1&pageSize=50', { token })
    assert.equal(res.code, 200)
    assert.equal((res.data as { total: number }).total, 22)
  }))

test('permissions search forbidden without permission:list', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/permissions/search', { token })
    assert.equal(res.code, 403)
  }, rolelessSeed()))

test('permission detail success and 404', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const ok = await api(baseUrl, 'GET', '/api/permissions/1', { token })
    assert.equal(ok.code, 200)
    assert.equal((ok.data as { code: string }).code, 'user:list')

    const missing = await api(baseUrl, 'GET', '/api/permissions/999', { token })
    assert.equal(missing.code, 404)
  }))

test('permission detail forbidden without permission:read', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const res = await api(baseUrl, 'GET', '/api/permissions/1', { token })
    assert.equal(res.code, 403)
  }, rolelessSeed()))

test('permission create success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/permissions', {
      token,
      body: { code: 'user:export', name: '导出用户', module: 'user' },
    })
    assert.equal(res.code, 200)
    assert.equal((res.data as { code: string }).code, 'user:export')
  }))

test('permission create validation', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const missing = await api(baseUrl, 'POST', '/api/permissions', { token, body: { name: '缺码', module: 'user' } })
    assert.equal(missing.code, 400)

    const badModule = await api(baseUrl, 'POST', '/api/permissions', {
      token,
      body: { code: 'x:y', name: 'x', module: 'nope' },
    })
    assert.equal(badModule.code, 400)
  }))

test('permission create duplicate code', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/permissions', {
      token,
      body: { code: 'user:list', name: '重复', module: 'user' },
    })
    assert.equal(res.code, 400)
  }))

test('permission create forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'POST', '/api/permissions', {
      token,
      body: { code: 'x:y', name: 'x', module: 'user' },
    })
    assert.equal(res.code, 403)
  }))

test('permission update name success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'PUT', '/api/permissions/1', { token, body: { name: '查看用户列表' } })
    assert.equal(res.code, 200)
    assert.equal((res.data as { name: string }).name, '查看用户列表')
  }))

test('permission update immutable code', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'PUT', '/api/permissions/1', { token, body: { code: 'user:renamed' } })
    assert.equal(res.code, 400)
  }))

test('permission update forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'PUT', '/api/permissions/1', { token, body: { name: 'x' } })
    assert.equal(res.code, 403)
  }))

test('permission delete used forbidden', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'DELETE', '/api/permissions/1', { token })
    assert.equal(res.code, 400)
  }))

test('permission delete unreferenced success', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const created = await api(baseUrl, 'POST', '/api/permissions', {
      token,
      body: { code: 'user:export', name: '导出用户', module: 'user' },
    })
    const id = (created.data as { id: number }).id
    const res = await api(baseUrl, 'DELETE', `/api/permissions/${id}`, { token })
    assert.equal(res.code, 200)
  }))

test('permission delete 404', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'DELETE', '/api/permissions/999', { token })
    assert.equal(res.code, 404)
  }))

test('permission delete forbidden for viewer', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'viewer')
    const res = await api(baseUrl, 'DELETE', '/api/permissions/1', { token })
    assert.equal(res.code, 403)
  }))

// ==================== 工作台 ====================

test('dashboard summary requires login and returns counts', () =>
  withServer(async (baseUrl) => {
    assert.equal((await api(baseUrl, 'GET', '/api/dashboard/summary')).code, 401)

    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/dashboard/summary', { token })
    assert.equal(res.code, 200)
    const data = res.data as { totalUsers: number; totalRoles: number; totalPermissions: number }
    assert.equal(data.totalUsers, 6)
    assert.equal(data.totalRoles, 3)
    assert.equal(data.totalPermissions, 22)
  }))

// ==================== 路由 ====================

test('unknown api route returns 404', () =>
  withServer(async (baseUrl) => {
    const res = await api(baseUrl, 'GET', '/api/not-exists')
    assert.equal(res.code, 404)
  }))
