import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authService } from '@/services/auth.service'

/**
 * 模块级缓存：以 token 为 key 缓存权限码集合，避免跨账号复用上一账号的权限
 * （退出后换低权限账号登录时必须重拉）。
 */
let cachedToken: string | null = null
let cachedCodes: Set<string> | null = null

/**
 * 当前用户权限状态仓库：菜单 / 按钮 / 路由守卫统一消费 hasPerm。
 */
export const usePermissionStore = defineStore('permission', () => {
  const codes = ref<Set<string>>(new Set())
  const isSuperuser = ref(false)
  const loaded = ref(false)
  const loading = ref(false)
  const error = ref('')

  /** 是否拥有某权限码；超管直接放行 */
  function hasPerm(code: string): boolean {
    return isSuperuser.value || codes.value.has(code)
  }

  function setSuperuser(value: boolean): void {
    isSuperuser.value = value
  }

  /** 清空权限状态与缓存（退出登录 / 切换账号时调用） */
  function reset(): void {
    cachedToken = null
    cachedCodes = null
    codes.value = new Set()
    isSuperuser.value = false
    loaded.value = false
    error.value = ''
  }

  /** 拉取当前用户权限码；按 token 键控缓存 */
  async function fetchPermissions(): Promise<void> {
    const token = authService.getToken()
    if (!token) {
      reset()
      return
    }
    if (cachedToken === token && cachedCodes) {
      codes.value = new Set(cachedCodes)
      loaded.value = true
      return
    }

    loading.value = true
    error.value = ''
    try {
      const list = await authService.mePermissions()
      const set = new Set(list)
      codes.value = set
      cachedToken = token
      cachedCodes = set
      loaded.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '权限加载失败'
      codes.value = new Set()
      loaded.value = false
    } finally {
      loading.value = false
    }
  }

  return { codes, isSuperuser, loaded, loading, error, hasPerm, setSuperuser, reset, fetchPermissions }
})
