import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { startBackend, type TestBackend } from './_backend'
import { dashboardApi } from '../../src/apis/dashboard'
import { expectReject, loginAs, logout } from './_auth'

const PORT = 8025
let backend: TestBackend

before(async () => {
  backend = await startBackend({ port: PORT, dbName: 'test_final_dashboard.db' })
})

after(async () => {
  await backend.stop()
})

test('管理员工作台统计映射为 camelCase', async () => {
  await loginAs('admin')
  const summary = await dashboardApi.summary()
  assert.deepEqual(summary, { totalUsers: 3, totalRoles: 3, totalPermissions: 71 })
})

test('运营账号可见同一份统计（dashboard:read）', async () => {
  await loginAs('ops')
  const summary = await dashboardApi.summary()
  assert.equal(summary.totalUsers, 3)
  assert.equal(summary.totalPermissions, 71)
})

test('只读账号可见工作台统计', async () => {
  await loginAs('viewer')
  const summary = await dashboardApi.summary()
  assert.equal(summary.totalRoles, 3)
})

test('未登录访问工作台统计返回 401', async () => {
  logout()
  await expectReject(() => dashboardApi.summary(), '未登录')
})
