import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { startBackend, type TestBackend } from './_backend'
import { authApi } from '../../src/apis/auth'
import { getAuthToken } from '../../src/apis/http'
import { expectReject, loginAs, logout } from './_auth'

const PORT = 8021
let backend: TestBackend

before(async () => {
  backend = await startBackend({ port: PORT, dbName: 'test_final_auth.db' })
})

after(async () => {
  await backend.stop()
})

test('管理员通过真实后端登录成功', async () => {
  const session = await loginAs('admin')
  assert.ok(session.token.length > 20, 'token 应非空')
  assert.equal(session.user.username, 'admin')
  assert.equal(session.user.isSuperuser, true)
  assert.equal(session.user.isActive, true)
  assert.equal(session.user.dataScope, 'all')
  assert.equal(getAuthToken(), session.token)
})

test('登录后可拉取 71 个权限码且按字典序返回', async () => {
  await loginAs('admin')
  const codes = await authApi.mePermissions()
  assert.equal(codes.length, 71)
  assert.deepEqual(codes, [...codes].sort())
  assert.ok(codes.includes('agent:list'))
  assert.ok(codes.includes('approval:audit'))
  assert.ok(!codes.includes('auth:captcha'))
})

test('me 返回带角色的用户信息', async () => {
  await loginAs('admin')
  const me = await authApi.me()
  assert.equal(me.username, 'admin')
  assert.equal(me.roleIds.length, 1)
  assert.match(me.createdAt, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
})

test('只读账号权限码为 23 个且不含写权限', async () => {
  await loginAs('viewer')
  const codes = await authApi.mePermissions()
  assert.equal(codes.length, 23)
  assert.ok(codes.includes('user:read'))
  assert.ok(!codes.includes('user:create'))
  assert.ok(!codes.includes('system:audit'))
})

test('运营账号权限码为 45 个（含审批授权）', async () => {
  await loginAs('ops')
  const codes = await authApi.mePermissions()
  assert.equal(codes.length, 45)
  assert.ok(codes.includes('conversation:annotate'))
  assert.ok(!codes.includes('user:delete'))
})

test('密码错误由后端返回业务码 401', async () => {
  const message = await expectReject(
    () => authApi.login({ username: 'admin', password: 'wrong-password' }),
    '用户名或密码错误',
  )
  assert.match(message, /用户名或密码错误/)
})

test('未登录访问受保护接口返回 401', async () => {
  logout()
  await expectReject(() => authApi.me(), '未登录')
})

test('退出登录后 token 被清空', async () => {
  await loginAs('admin')
  assert.ok(getAuthToken())
  logout()
  assert.equal(getAuthToken(), null)
})
