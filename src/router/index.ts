import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { usePermissionStore } from '@/store/permission'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/Login.vue'),
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/pages/Forbidden.vue'),
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/pages/Dashboard.vue'),
      },
      {
        path: 'system/users',
        name: 'system-users',
        component: () => import('@/pages/system/Users.vue'),
        meta: { permission: 'user:list' },
      },
      {
        path: 'system/roles',
        name: 'system-roles',
        component: () => import('@/pages/system/Roles.vue'),
        meta: { permission: 'role:list' },
      },
      {
        path: 'system/permissions',
        name: 'system-permissions',
        component: () => import('@/pages/system/Permissions.vue'),
        meta: { permission: 'permission:list' },
      },
      {
        path: 'system/api-keys',
        name: 'system-api-keys',
        component: () => import('@/pages/system/Placeholder.vue'),
        meta: { permission: 'system:api_keys', title: 'API 密钥' },
      },
      {
        path: 'system/audit',
        name: 'system-audit',
        component: () => import('@/pages/system/Placeholder.vue'),
        meta: { permission: 'system:audit', title: '审计日志' },
      },
      {
        path: 'system/alerts',
        name: 'system-alerts',
        component: () => import('@/pages/system/Placeholder.vue'),
        meta: { permission: 'system:alerts', title: '告警规则' },
      },
      {
        path: 'system/settings',
        name: 'system-settings',
        component: () => import('@/pages/system/Placeholder.vue'),
        meta: { permission: 'system:settings', title: '系统配置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

/**
 * 全局路由守卫：
 * - 已登录但未恢复用户信息时先恢复（刷新页面场景）
 * - 未登录访问受保护页 → /login（携带来源）
 * - 已登录访问 /login → 工作台
 * - 目标路由带 meta.permission 且无权限 → /403
 */
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  const perm = usePermissionStore()

  if (auth.token && !auth.user) {
    try {
      await auth.restore()
    } catch {
      auth.logout()
    }
  }

  if (to.path === '/login') {
    return auth.isLoggedIn ? '/' : true
  }

  if (!auth.isLoggedIn) {
    return to.fullPath !== '/' ? { path: '/login', query: { redirect: to.fullPath } } : { path: '/login' }
  }

  // 每次导航都校验权限（fetchPermissions 按 token 键控缓存，命中即复用），
  // 确保跨标签页 token 变化或退出重登后不会残留上一账号的权限集合。
  await perm.fetchPermissions()

  const required = to.meta.permission as string | undefined
  if (required && !perm.hasPerm(required)) {
    return { path: '/403' }
  }

  return true
})

export default router
