import type { Directive } from 'vue'
import { usePermissionStore } from '@/store/permission'

/**
 * v-permission="'user:create'"：无对应权限时移除元素。
 * 在 mounted 中移除，避免 patch 阶段原地删除节点引发渲染冲突。
 */
export const vPermission: Directive<HTMLElement, string> = {
  mounted(el, binding) {
    const store = usePermissionStore()
    if (binding.value && !store.hasPerm(binding.value)) {
      el.parentNode?.removeChild(el)
    }
  },
}
