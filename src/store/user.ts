import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userService } from '@/services/user.service'
import type { CreateUserData } from '@/apis/user'
import type { User } from '@/types'

/** 用户状态仓库：维护用户列表的分页、搜索与增删 / 分配角色操作 */
export const useUserStore = defineStore('user', () => {
  const list = ref<User[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const keyword = ref('')
  const loading = ref(false)
  const error = ref('')

  async function fetchList(params?: { page?: number; pageSize?: number; keyword?: string }) {
    page.value = params?.page ?? page.value
    pageSize.value = params?.pageSize ?? pageSize.value
    keyword.value = params?.keyword ?? keyword.value
    loading.value = true
    error.value = ''
    try {
      const result = await userService.list({ page: page.value, pageSize: pageSize.value, keyword: keyword.value })
      list.value = result.list
      total.value = result.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: CreateUserData) {
    await userService.create(data)
    await fetchList()
  }

  async function removeUser(id: number) {
    await userService.remove(id)
    await fetchList()
  }

  async function assignRoles(id: number, roleIds: number[]) {
    await userService.assignRoles(id, roleIds)
    await fetchList()
  }

  return { list, total, page, pageSize, keyword, loading, error, fetchList, createUser, removeUser, assignRoles }
})
