import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { startBackend, type TestBackend } from './_backend'
import { roleApi } from '../../src/apis/role'
import { expectReject, loginAs } from './_auth'

const PORT = 8023
let backend: TestBackend
const CREATED_CODE = 'auditor_final'

before(async () => {
  backend = await startBackend({ port: PORT, dbName: 'test_final_role.db' })
  await loginAs('admin')
})

after(async () => {
  await backend.stop()
})

test('角色列表映射 permissions → permissionCodes 与 isSystem', async () => {
  const roles = await roleApi.listAll()
  assert.equal(roles.length, 3)
  const superAdmin = roles.find((role) => role.code === 'super_admin')
  assert.ok(superAdmin)
  assert.equal(superAdmin.isSystem, true)
  assert.equal(superAdmin.permissionCodes.length, 71)
  const viewer = roles.find((role) => role.code === 'viewer')
  assert.ok(viewer)
  assert.equal(viewer.isSystem, false)
  assert.equal(viewer.permissionCodes.length, 23)
})

test('分页搜索角色', async () => {
  const page = await roleApi.search({ page: 1, pageSize: 10, keyword: 'ops' })
  assert.equal(page.total, 1)
  assert.equal(page.list[0].code, 'ops_admin')
})

test('创建角色并按权限码分配权限（两步提交）', async () => {
  const created = await roleApi.create({
    code: CREATED_CODE,
    name: '审计员',
    description: '联调测试角色',
    permissionCodes: ['agent:list', 'agent:read'],
  })
  assert.equal(created.code, CREATED_CODE)
  assert.equal(created.isSystem, false)
  assert.deepEqual(new Set(created.permissionCodes), new Set(['agent:list', 'agent:read']))
})

test('分配权限后权限码集合更新', async () => {
  const roles = await roleApi.listAll()
  const target = roles.find((role) => role.code === CREATED_CODE)
  assert.ok(target)
  const updated = await roleApi.assignPermissions(target.id, [
    'agent:list',
    'agent:read',
    'agent:create',
  ])
  assert.deepEqual(
    new Set(updated.permissionCodes),
    new Set(['agent:list', 'agent:read', 'agent:create']),
  )
})

test('更新角色名称（角色码保持不变）', async () => {
  const roles = await roleApi.listAll()
  const target = roles.find((role) => role.code === CREATED_CODE)
  assert.ok(target)
  const updated = await roleApi.update(target.id, { code: 'ignored_code', name: '高级审计员' })
  assert.equal(updated.name, '高级审计员')
  assert.equal(updated.code, CREATED_CODE)
})

test('删除角色后列表恢复为 3 个', async () => {
  const roles = await roleApi.listAll()
  const target = roles.find((role) => role.code === CREATED_CODE)
  assert.ok(target)
  await roleApi.remove(target.id)
  assert.equal((await roleApi.listAll()).length, 3)
})

test('角色不存在返回 404 文案', async () => {
  await expectReject(() => roleApi.detail(99999), '角色不存在')
})

test('只读账号创建角色被拒绝（403）', async () => {
  await loginAs('viewer')
  await expectReject(
    () => roleApi.create({ code: 'forbidden_role', name: '无权创建' }),
    '没有权限',
  )
})
