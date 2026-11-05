import { test, before, after } from 'node:test'
import assert from 'node:assert/strict'
import { startMockServer, type MockServer } from './_helpers.ts'

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

let srv: MockServer

before(async () => {
  srv = await startMockServer()
})

after(async () => {
  await srv.close()
})

async function api(method: string, path: string, opts: { token?: string; body?: unknown } = {}) {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json'
  const res = await fetch(`${srv.baseUrl}${path}`, {
    method,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })
  return res.json() as Promise<{ code: number; message: string; data: unknown }>
}

async function login(username: string, password = '123456') {
  const captcha = await api('GET', '/api/auth/captcha')
  const captchaData = (captcha as { data: { captchaId: string; text: string } }).data
  return api('POST', '/api/auth/login', {
    body: { username, password, captchaId: captchaData.captchaId, captcha: captchaData.text },
  })
}

test('auth login success', async () => {
  const res = await login('admin')
  assert.equal(res.code, 200)
  const data = res.data as { token: string; user: { username: string } }
  assert.ok(data.token)
  assert.equal(data.user.username, 'admin')
})

test('auth login wrong captcha', async () => {
  const captcha = await api('GET', '/api/auth/captcha')
  const captchaData = (captcha as { data: { captchaId: string } }).data
  const res = await api('POST', '/api/auth/login', {
    body: { username: 'admin', password: '123456', captchaId: captchaData.captchaId, captcha: 'XXXX' },
  })
  assert.equal(res.code, 400)
})

test('me requires login', async () => {
  const res = await api('GET', '/api/users/me')
  assert.equal(res.code, 401)
})

test('me permissions superuser dedup sorted', async () => {
  const loginRes = await login('admin')
  const token = (loginRes.data as { token: string }).token
  const res = await api('GET', '/api/users/me/permissions', { token })
  assert.equal(res.code, 200)
  assert.deepEqual(res.data, ALL_CODES_SORTED)
})
