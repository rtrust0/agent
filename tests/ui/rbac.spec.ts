import { test, expect, type Page } from '@playwright/test'

type IdentityLabel = '超级管理员' | '运营管理员' | '只读观察者'

/**
 * 登录：点击演示账号填充用户名/密码后提交。
 * 后端为真实 FastAPI（Playwright 启动），不存在验证码步骤。
 */
async function loginAs(page: Page, label: IdentityLabel) {
  await page.goto('/login')
  await page.getByRole('button', { name: label }).click()
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL('/')
}

test('admin sees all system menu items', async ({ page }) => {
  await loginAs(page, '超级管理员')
  for (const name of ['用户管理', '角色管理', '权限管理', 'API 密钥', '审计日志', '告警规则', '系统配置']) {
    await expect(page.getByRole('link', { name })).toBeVisible()
  }
})

test('viewer menu hides write / system modules', async ({ page }) => {
  await loginAs(page, '只读观察者')
  await expect(page.getByRole('link', { name: '用户管理' })).toBeVisible()
  await expect(page.getByRole('link', { name: '角色管理' })).toBeVisible()
  await expect(page.getByRole('link', { name: '权限管理' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'API 密钥' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: '审计日志' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: '系统配置' })).toHaveCount(0)
  // 演示用的身份切换器已整体移除，任何账号都不应出现
  await expect(page.locator('.switcher')).toHaveCount(0)
})

test('viewer sees no create / delete / assign buttons on users page', async ({ page }) => {
  await loginAs(page, '只读观察者')
  await page.getByRole('link', { name: '用户管理' }).click()
  await expect(page).toHaveURL('/system/users')
  await expect(page.getByRole('button', { name: '添加用户' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '删除' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '分配角色' })).toHaveCount(0)
})

test('ops sees create but not delete / assign buttons on users page', async ({ page }) => {
  await loginAs(page, '运营管理员')
  await page.getByRole('link', { name: '用户管理' }).click()
  await expect(page.getByRole('button', { name: '添加用户' })).toBeVisible()
  await expect(page.getByRole('button', { name: '删除' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '分配角色' })).toHaveCount(0)
})

test('admin sees role action buttons', async ({ page }) => {
  await loginAs(page, '超级管理员')
  await page.getByRole('link', { name: '角色管理' }).click()
  await expect(page.getByRole('button', { name: '创建角色' })).toBeVisible()
  await expect(page.getByRole('button', { name: '编辑' }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: '分配权限' }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: '删除' }).first()).toBeVisible()
})

test('viewer permissions page renders backend matrix（71 权限 / 14 模块）', async ({ page }) => {
  await loginAs(page, '只读观察者')
  await page.getByRole('link', { name: '权限管理' }).click()
  await expect(page.getByRole('button', { name: '创建权限' })).toHaveCount(0)

  await page.getByRole('button', { name: '矩阵' }).click()
  await expect(page.getByText('权限矩阵')).toBeVisible()
  await expect(page.locator('.matrix__dot--on').first()).toBeVisible()
  // 权限码 1 列 + 3 个角色列
  await expect(page.locator('.matrix thead th')).toHaveCount(4)
  // 71 条权限 + 14 个模块分组 = 85 行（表头另计）
  await expect(page.locator('tbody .matrix__code')).toHaveCount(71)
  await expect(page.locator('.matrix__module-row')).toHaveCount(14)
})

test('admin creates and deletes a user through the real backend', async ({ page }) => {
  const username = `e2e_user_${Date.now()}`
  await loginAs(page, '超级管理员')
  await page.getByRole('link', { name: '用户管理' }).click()
  await expect(page).toHaveURL('/system/users')

  await page.getByRole('button', { name: '添加用户' }).click()
  await page.getByLabel('用户名').fill(username)
  await page.getByLabel('邮箱').fill(`${username}@example.com`)
  await page.getByLabel('密码').fill('123456')
  await page.getByRole('button', { name: '创建' }).click()

  await expect(page.getByText(`${username}@example.com`)).toBeVisible()

  const row = page.locator('tr', { hasText: username })
  await row.getByRole('button', { name: '删除' }).click()
  await page.getByRole('button', { name: '删除', exact: true }).last().click()
  await expect(page.getByText(`${username}@example.com`)).toHaveCount(0)
})

test('ops is redirected to /403 for an unauthorized system route', async ({ page }) => {
  await loginAs(page, '运营管理员')
  await page.goto('/system/api-keys')
  await expect(page).toHaveURL('/403')
  await expect(page.getByText('无权访问该页面')).toBeVisible()
})

test('unauthenticated access redirects to login with redirect query', async ({ page }) => {
  await page.goto('/system/users')
  await expect(page).toHaveURL(/\/login\?redirect=/)
  await expect(page.getByRole('heading', { name: '登录' })).toBeVisible()
})

test('logout then login as viewer shrinks menu without reload', async ({ page }) => {
  await loginAs(page, '超级管理员')
  await expect(page.getByRole('link', { name: 'API 密钥' })).toBeVisible()

  // 退出登录（客户端导航，无整页刷新）
  await page.locator('.userbox__logout').click()
  await expect(page).toHaveURL(/\/login/)

  // 以 viewer 重新登录
  await page.getByRole('button', { name: '只读观察者' }).click()
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL('/')

  await expect(page.getByRole('link', { name: 'API 密钥' })).toHaveCount(0)
  await expect(page.locator('.userbox__name')).toHaveText('viewer')
})

test('dashboard renders stats and permission chips from backend', async ({ page }) => {
  await loginAs(page, '超级管理员')

  // 统计卡片：用户 3 / 角色 3 / 权限 71（均来自 GET /dashboard/stats）
  await expect(page.locator('.stat__value')).toHaveText(['3', '3', '71'])
  // 当前身份权限：超管拥有全部 71 项
  await expect(page.getByText('当前身份权限（71 项）')).toBeVisible()
  // 权限矩阵按后端模块分组渲染（14 个模块分组标题）
  await expect(page.locator('.matrix thead th')).toHaveCount(4)
})

test('identity switcher is removed from the layout', async ({ page }) => {
  await loginAs(page, '超级管理员')
  // 顶栏不再提供身份切换按钮，避免演示用的“一键提权”入口
  await expect(page.locator('.switcher')).toHaveCount(0)
  await expect(page.getByRole('group', { name: '身份切换' })).toHaveCount(0)
  // 退出后可通过登录页换账号
  await page.locator('.userbox__logout').click()
  await expect(page).toHaveURL(/\/login/)
})
