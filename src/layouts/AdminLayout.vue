<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { usePermission } from '@/composables/usePermission'
import { useToast } from '@/composables/useToast'

interface MenuItem {
  to: string
  label: string
  permission?: string
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { hasPerm } = usePermission()
const { toast } = useToast()

const platformItems: MenuItem[] = [{ to: '/', label: '工作台' }]

const systemItems: MenuItem[] = [
  { to: '/system/users', label: '用户管理', permission: 'user:list' },
  { to: '/system/roles', label: '角色管理', permission: 'role:list' },
  { to: '/system/permissions', label: '权限管理', permission: 'permission:list' },
  { to: '/system/api-keys', label: 'API 密钥', permission: 'system:api_keys' },
  { to: '/system/audit', label: '审计日志', permission: 'system:audit' },
  { to: '/system/alerts', label: '告警规则', permission: 'system:alerts' },
  { to: '/system/settings', label: '系统配置', permission: 'system:settings' },
]

const ICONS: Record<string, string> = {
  '/': 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  '/system/users':
    'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0 8 4 4 0 0 0 0-8M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
  '/system/roles': 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  '/system/permissions':
    'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4',
  '/system/api-keys': 'M16 18l6-6-6-6M8 6l-6 6 6 6',
  '/system/audit': 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8',
  '/system/alerts': 'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0',
  '/system/settings':
    'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
}

/** 按权限过滤后的系统管理子菜单；全无权限时父菜单整体隐藏 */
const visibleSystemItems = computed(() =>
  systemItems.filter((item) => !item.permission || hasPerm(item.permission)),
)

const breadcrumbs = computed(() => {
  if (route.path === '/') return ['工作台']
  const item = [...platformItems, ...systemItems].find((i) => i.to === route.path)
  return ['系统管理', item?.label ?? '']
})

const identities = [
  { username: 'admin', label: '超级管理员' },
  { username: 'ops', label: '运营管理员' },
  { username: 'viewer', label: '只读观察者' },
]

const switching = ref(false)
const activeUsername = computed(() => auth.user?.username ?? '')
const currentRoleLabel = computed(
  () => identities.find((i) => i.username === activeUsername.value)?.label ?? '',
)

async function onSwitch(username: string) {
  if (switching.value || username === activeUsername.value) return
  switching.value = true
  try {
    await auth.switchIdentity(username)
    window.location.reload()
  } catch (e) {
    toast('error', e instanceof Error ? e.message : '身份切换失败')
    switching.value = false
  }
}

async function onLogout() {
  auth.logout()
  await router.replace('/login')
}
</script>

<template>
  <div class="admin">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand__mark" aria-hidden="true" />
        <div class="brand__text">
          <strong class="brand__name">辰光</strong>
          <span class="brand__sub">Agent 平台</span>
        </div>
      </div>

      <nav class="nav">
        <p class="nav__group">平台</p>
        <RouterLink
          v-for="item in platformItems"
          :key="item.to"
          :to="item.to"
          class="nav__item"
          :class="{ 'nav__item--active': route.path === item.to }"
        >
          <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="ICONS[item.to]" />
          </svg>
          <span>{{ item.label }}</span>
        </RouterLink>

        <template v-if="visibleSystemItems.length > 0">
          <p class="nav__group">系统管理</p>
          <RouterLink
            v-for="item in visibleSystemItems"
            :key="item.to"
            :to="item.to"
            class="nav__item"
            :class="{ 'nav__item--active': route.path === item.to }"
          >
            <svg class="nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path :d="ICONS[item.to]" />
            </svg>
            <span>{{ item.label }}</span>
          </RouterLink>
        </template>
      </nav>

      <div class="userbox">
        <div class="userbox__info">
          <span class="userbox__name">{{ auth.user?.username ?? '未登录' }}</span>
          <span class="userbox__role">{{ currentRoleLabel }}</span>
        </div>
        <button class="userbox__logout" type="button" @click="onLogout">退出</button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="crumbs">
          <span v-for="(crumb, index) in breadcrumbs" :key="crumb" class="crumbs__item">
            {{ crumb }}
            <span v-if="index < breadcrumbs.length - 1" class="crumbs__sep">/</span>
          </span>
        </div>

        <div class="switcher" role="group" aria-label="身份切换">
          <button
            v-for="identity in identities"
            :key="identity.username"
            class="switcher__btn"
            :class="{ 'switcher__btn--active': identity.username === activeUsername }"
            type="button"
            :disabled="switching"
            @click="onSwitch(identity.username)"
          >
            {{ identity.label }}
          </button>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin {
  display: flex;
  min-height: 100dvh;
  background: var(--bg);
}
.sidebar {
  width: 248px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--navy-900);
  color: #c9d3e3;
  position: sticky;
  top: 0;
  height: 100dvh;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand__mark {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--dawn), #b57d24);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.brand__name {
  color: #fff;
  font-size: 15px;
  letter-spacing: 0.04em;
}
.brand__sub {
  font-size: 11px;
  color: #8b97ab;
}
.nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 10px;
}
.nav__group {
  padding: 12px 12px 6px;
  font-size: 11px;
  letter-spacing: 0.12em;
  color: #6f7f99;
}
.nav__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  margin-bottom: 2px;
  border-radius: 6px;
  color: #b9c4d6;
  font-size: 13px;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.nav__item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}
.nav__item--active {
  background: var(--brand);
  color: #fff;
}
.nav__icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
.userbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.userbox__info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}
.userbox__name {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
}
.userbox__role {
  font-size: 11.5px;
  color: #8b97ab;
}
.userbox__logout {
  height: 28px;
  padding: 0 10px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 6px;
  background: transparent;
  color: #c9d3e3;
  font-size: 12px;
}
.userbox__logout:hover {
  background: rgba(255, 255, 255, 0.08);
}
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 32px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 20;
}
.crumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-2);
  font-size: 12.5px;
}
.crumbs__sep {
  margin-left: 6px;
  color: var(--ink-3);
}
.switcher {
  display: flex;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f3f5f8;
}
.switcher__btn {
  height: 28px;
  padding: 0 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ink-2);
  font-size: 12.5px;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.switcher__btn:hover:not(:disabled) {
  color: var(--ink);
}
.switcher__btn--active {
  background: #fff;
  color: var(--navy-900);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
}
.switcher__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.content {
  flex: 1;
  min-width: 0;
}
@media (max-width: 900px) {
  .sidebar {
    width: 72px;
  }
  .brand__text,
  .nav__item span,
  .nav__group,
  .userbox__info {
    display: none;
  }
  .nav__item {
    justify-content: center;
  }
  .userbox {
    justify-content: center;
  }
  .topbar {
    padding: 0 16px;
  }
}
</style>
