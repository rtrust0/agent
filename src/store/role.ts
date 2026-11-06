import { defineStore } from 'pinia'
import { ref } from 'vue'
import { roleService } from '@/services/role.service'
import type { Role } from '@/types'

/** 角色状态仓库：维护全量角色列表（分配角色 / 分配权限弹窗共用） */
export const useRoleStore = defineStore('role', () => {
  const roles = ref<Role[]>([])
  const loading = ref(false)
  const error = ref('')

  async function fetchAll() {
    loading.value = true
    error.value = ''
    try {
      roles.value = await roleService.listAll()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  return { roles, loading, error, fetchAll }
})
