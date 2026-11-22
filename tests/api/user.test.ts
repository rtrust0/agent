import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { startBackend, type TestBackend } from './_backend'
import { userApi } from '../../src/apis/user'
import { roleApi } from '../../src/apis/role'
import { expectReject, loginAs } from './_auth'

const PORT = 8022
let backend: TestBackend
const CREATED = 'final_user'

before(async () => {
  backend = await startBackend({ port: PORT, dbName: 'test_final_user.db' })
  await loginAs('admin')
})

after(async () => {
  await backend.stop()
})

test('全量用户列表返回 seed 的 3 个账号', async () => {
  const users = await userApi.listAll()
  assert.equal(users.length, 3)
  assert.deepEqual(
    users.map((user) => user.username),
    ['admin', 'ops', 'viewer'],
  )
})

test('分页参数从 camelCase 映射为后端 page_size', async () => {
  const page = await userApi.search({ page: 2, pageSize: 2 })
  assert.equal(page.total, 3)
  assert.equal(page.page, 2)
  assert.equal(page.pageSize, 2)
  assert.equal(page.list.length, 1)
})

test('关键字搜索命中单个用户', async () => {
  const page = await userApi.search({ keyword: 'ops' })
  assert.equal(page.total, 1)
  assert.equal(page.list[0].username, 'ops')
})

test('创建用户并映射 roles → roleIds', async () => {
  const roles = await roleApi.listAll()
  const viewerRole = roles.find((role) => role.code === 'viewer')
  assert.ok(viewerRole)

  const created = await userApi.create({
    username: CREATED,
    email: `${CREATED}@example.com`,
    password: '123456',
    roleIds: [viewerRole.id],
  })
  assert.equal(created.username, CREATED)
  assert.equal(created.isActive, true)
  assert.equal(created.isSuperuser, false)
  assert.deepEqual(created.roleIds, [viewerRole.id])
  assert.equal(created.dataScope, 'own')
})

test('查看与调整用户角色', async () => {
  const page = await userApi.search({ keyword: CREATED })
  const target = page.list[0]
  const roles = await userApi.readRoles(target.id)
  assert.equal(roles.length, 1)
  assert.equal(roles[0].code, 'viewer')
  assert.equal(roles[0].permissionCodes.length, 23)

  const cleared = await userApi.assignRoles(target.id, [])
  assert.deepEqual(cleared.roleIds, [])
  assert.deepEqual(await userApi.readRoles(target.id), [])
})

test('详情映射 createdAt / dataScope 字段', async () => {
  const page = await userApi.search({ keyword: CREATED })
  const detail = await userApi.detail(page.list[0].id)
  assert.equal(detail.email, `${CREATED}@example.com`)
  assert.match(detail.createdAt, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
  assert.equal(detail.dataScope, 'own')
})

test('删除用户后搜索结果为空', async () => {
  const page = await userApi.search({ keyword: CREATED })
  await userApi.remove(page.list[0].id)
  const after = await userApi.search({ keyword: CREATED })
  assert.equal(after.total, 0)
})

test('只读账号创建用户被后端拒绝（403）', async () => {
  await loginAs('viewer')
  await expectReject(
    () =>
      userApi.create({
        username: 'forbidden_user',
        email: 'forbidden@example.com',
        password: '123456',
      }),
    '没有权限',
  )
})

test('运营账号删除用户被后端拒绝（403）', async () => {
  await loginAs('ops')
  await expectReject(() => userApi.remove(1), '没有权限')
})
