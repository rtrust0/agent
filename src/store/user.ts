import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userService } from '@/services/user.service'
import type { User } from '@/types'

/**
 * 用户状态仓库：封装用户列表的加载状态、数据与操作，
 * 页面只与 store 交互，业务调用收敛到 services 层。
 */
export const useUserStore = defineStore('user', () => {
  const list = ref<User[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref('')

  async function fetchList(page = 1, pageSize = 10) {
    loading.value = true
    error.value = ''
    try {
      const result = await userService.list({ page, pageSize })
      list.value = result.list
      total.value = result.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: { name: string; email: string; role: string }) {
    loading.value = true
    error.value = ''
    try {
      await userService.create(data)
      await fetchList()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { list, total, loading, error, fetchList, createUser }
})
