import { test, expect, type Page } from '@playwright/test'

type IdentityLabel = '超级管理员' | '运营管理员' | '只读观察者'

/** 通过登录页的演示账号按钮完成登录（验证码文本从页面直接读取） */
async function loginAs(page: Page, label: IdentityLabel) {
  await page.goto('/login')
  await page.getByRole('button', { name: label }).click()

  const captchaBox = page.locator('.captcha__box')
  await expect(captchaBox).toHaveText(/^[A-Z0-9]{4}$/)
  const captcha = (await captchaBox.innerText()).trim()

  await page.getByLabel('验证码').fill(captcha)
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

test('viewer permissions page hides create and renders matrix', async ({ page }) => {
  await loginAs(page, '只读观察者')
  await page.getByRole('link', { name: '权限管理' }).click()
  await expect(page.getByRole('button', { name: '创建权限' })).toHaveCount(0)

  await page.getByRole('button', { name: '矩阵' }).click()
  await expect(page.getByText('权限矩阵')).toBeVisible()
  await expect(page.locator('.matrix__dot--on').first()).toBeVisible()
  // 22 权限行 + 4 模块行 = 26 行；权限码 + 3 角色 = 4 列
  await expect(page.locator('.matrix thead th')).toHaveCount(4)
  await expect(page.locator('.matrix tbody tr')).toHaveCount(26)
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
  const captchaBox = page.locator('.captcha__box')
  await expect(captchaBox).toHaveText(/^[A-Z0-9]{4}$/)
  await page.getByLabel('验证码').fill((await captchaBox.innerText()).trim())
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL('/')

  await expect(page.getByRole('link', { name: 'API 密钥' })).toHaveCount(0)
  await expect(page.locator('.userbox__name')).toHaveText('viewer')
})

test('identity switch recomputes menu and user box', async ({ page }) => {
  await loginAs(page, '超级管理员')
  await expect(page.getByRole('link', { name: 'API 密钥' })).toBeVisible()

  await page.getByRole('button', { name: '只读观察者' }).click()
  await page.waitForLoadState('load')

  await expect(page.locator('.userbox__name')).toHaveText('viewer')
  await expect(page.getByRole('link', { name: 'API 密钥' })).toHaveCount(0)
})
