import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authService } from '@/services/auth.service'
import { usePermissionStore } from './permission'
import type { User } from '@/types'

export interface LoginCredentials {
  username: string
  password: string
}

/**
 * 认证状态仓库：维护 token 与当前用户，登录后同步刷新权限码集合。
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(authService.getToken())
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref('')

  const isLoggedIn = computed(() => Boolean(token.value))

  /** 登录：持久化 token、记录用户、刷新权限 */
  async function login(credentials: LoginCredentials): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const session = await authService.login(credentials)
      token.value = session.token
      user.value = session.user
      const perm = usePermissionStore()
      perm.setSuperuser(session.user.isSuperuser)
      await perm.fetchPermissions()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '登录失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  /** 页面刷新后恢复当前用户信息（并同步超管标记） */
  async function restore(): Promise<void> {
    if (!token.value || user.value) return
    user.value = await authService.me()
    usePermissionStore().setSuperuser(user.value.isSuperuser)
  }

  /** 退出登录：清 token、用户与权限状态 */
  function logout(): void {
    authService.logout()
    token.value = null
    user.value = null
    usePermissionStore().reset()
  }

  return { token, user, loading, error, isLoggedIn, login, restore, logout }
})
