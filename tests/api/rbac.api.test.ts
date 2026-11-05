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

// ---------- 认证 ----------

test('auth login success', () =>
  withServer(async (baseUrl) => {
    const { token, user } = await login(baseUrl, 'admin')
    assert.ok(token)
    assert.equal(user.username, 'admin')
  }))

test('auth login wrong captcha', () =>
  withServer(async (baseUrl) => {
    const captcha = await api(baseUrl, 'GET', '/api/auth/captcha')
    const captchaData = captcha.data as { captchaId: string }
    const res = await api(baseUrl, 'POST', '/api/auth/login', {
      body: { username: 'admin', password: '123456', captchaId: captchaData.captchaId, captcha: 'XXXX' },
    })
    assert.equal(res.code, 400)
  }))

test('me requires login', () =>
  withServer(async (baseUrl) => {
    const res = await api(baseUrl, 'GET', '/api/users/me')
    assert.equal(res.code, 401)
  }))

test('me permissions superuser dedup sorted', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/me/permissions', { token })
    assert.equal(res.code, 200)
    assert.deepEqual(res.data, ALL_CODES_SORTED)
  }))

// ---------- 用户 ----------

test('users list requires login', () =>
  withServer(async (baseUrl) => {
    const noToken = await api(baseUrl, 'GET', '/api/users')
    assert.equal(noToken.code, 401)

    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users', { token })
    assert.equal(res.code, 200)
    assert.ok(Array.isArray(res.data))
    assert.equal((res.data as unknown[]).length, 6)
  }))

test('users list login only, no user:list permission required', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'nobody')
    const list = await api(baseUrl, 'GET', '/api/users', { token })
    assert.equal(list.code, 200)
    const search = await api(baseUrl, 'GET', '/api/users/search', { token })
    assert.equal(search.code, 403)
  }, rolelessSeed()))

test('user search pagination', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'GET', '/api/users/search?page=1&pageSize=2', { token })
    assert.equal(res.code, 200)
    const data = res.data as { list: unknown[]; total: number }
    assert.equal(data.total, 6)
    assert.equal(data.list.length, 2)
  }))

test('user create validation', () =>
  withServer(async (baseUrl) => {
    const { token } = await login(baseUrl, 'admin')
    const res = await api(baseUrl, 'POST', '/api/users', { token, body: { email: 'x@x.com', password: '123456' } })
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
    const created = res.data as { id: number; username: string }
    assert.equal(created.username, 'newuser')

    const list = await api(baseUrl, 'GET', '/api/users/search?page=1&pageSize=20', { token })
    assert.equal((list.data as { total: number }).total, 7)
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
