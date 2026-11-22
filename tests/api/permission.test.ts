import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { startBackend, type TestBackend } from './_backend'
import { permissionApi } from '../../src/apis/permission'
import { expectReject, loginAs } from './_auth'

const PORT = 8024
let backend: TestBackend
const CREATED_CODE = 'report:read'

before(async () => {
  backend = await startBackend({ port: PORT, dbName: 'test_final_permission.db' })
  await loginAs('admin')
})

after(async () => {
  await backend.stop()
})

test('权限目录 71 条、14 个模块（module 由后端派生）', async () => {
  const permissions = await permissionApi.listAll()
  assert.equal(permissions.length, 71)
  const modules = new Set(permissions.map((permission) => permission.module))
  assert.equal(modules.size, 14)
  for (const module of ['user', 'system', 'agent', 'knowledge', 'analytics']) {
    assert.ok(modules.has(module), `缺少模块 ${module}`)
  }
  assert.equal(permissions[0].module, 'user')
})

test('分页搜索权限码', async () => {
  const page = await permissionApi.search({ page: 1, pageSize: 20, keyword: 'agent:' })
  assert.equal(page.total, 8)
  assert.ok(page.list.every((permission) => permission.code.startsWith('agent:')))
})

test('权限详情返回名称与模块', async () => {
  const page = await permissionApi.search({ keyword: 'knowledge:reindex' })
  const detail = await permissionApi.detail(page.list[0].id)
  assert.equal(detail.code, 'knowledge:reindex')
  assert.equal(detail.module, 'knowledge')
})

test('创建权限时模块由权限码前缀自动派生', async () => {
  const created = await permissionApi.create({ code: CREATED_CODE, name: '报表查看', module: 'system' })
  assert.equal(created.code, CREATED_CODE)
  assert.equal(created.module, 'report')
  assert.equal(created.name, '报表查看')
})

test('权限码格式非法被后端拒绝', async () => {
  await expectReject(
    () => permissionApi.create({ code: 'Bad Code', name: '非法' }),
    '权限码格式',
  )
})

test('权限码重复被后端拒绝', async () => {
  await expectReject(
    () => permissionApi.create({ code: CREATED_CODE, name: '重复' }),
    '权限码已存在',
  )
})

test('更新权限名称（权限码不可改）', async () => {
  const page = await permissionApi.search({ keyword: CREATED_CODE })
  const updated = await permissionApi.update(page.list[0].id, { name: '报表导出' })
  assert.equal(updated.name, '报表导出')
  assert.equal(updated.code, CREATED_CODE)
})

test('删除权限后详情返回 404', async () => {
  const page = await permissionApi.search({ keyword: CREATED_CODE })
  await permissionApi.remove(page.list[0].id)
  await expectReject(() => permissionApi.detail(page.list[0].id), '权限不存在')
})

test('只读账号创建权限被拒绝（403）', async () => {
  await loginAs('viewer')
  await expectReject(
    () => permissionApi.create({ code: 'report:write', name: '无权创建' }),
    '没有权限',
  )
})
