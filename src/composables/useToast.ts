import { reactive } from 'vue'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  type: ToastType
  message: string
}

const state = reactive<{ items: ToastItem[] }>({ items: [] })
let seq = 0

/** 轻量全局 Toast：toast('success', '创建成功') */
export function useToast() {
  function toast(type: ToastType, message: string): void {
    const id = ++seq
    state.items.push({ id, type, message })
    window.setTimeout(() => {
      const index = state.items.findIndex((item) => item.id === id)
      if (index !== -1) state.items.splice(index, 1)
    }, 3200)
  }
  return { toast }
}

/** 供 AppToast 读取当前 Toast 队列 */
export function useToastItems() {
  return state.items
}
