import { storeToRefs } from 'pinia'
import { usePermissionStore } from '@/store/permission'

/**
 * 权限判断组合式函数：模板 / 脚本中统一通过 hasPerm 判断当前用户权限。
 * `loaded` 可用于区分"尚未加载"与"确实无权限"。
 */
export function usePermission() {
  const store = usePermissionStore()
  const { loaded, loading } = storeToRefs(store)

  function hasPerm(code: string): boolean {
    return store.hasPerm(code)
  }

  return { hasPerm, loaded, loading }
}
