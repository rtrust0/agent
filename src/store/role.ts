import { defineStore } from 'pinia'
import { ref } from 'vue'
import { roleService } from '@/services/role.service'
import type { CreateRoleData, UpdateRoleData } from '@/apis/role'
import type { Role } from '@/types'

/** 角色状态仓库：全量角色列表（供分配弹窗）+ 分页列表 + CRUD + 分配权限 */
export const useRoleStore = defineStore('role', () => {
  const roles = ref<Role[]>([])
  const list = ref<Role[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const keyword = ref('')
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

  async function fetchList(params?: { page?: number; pageSize?: number; keyword?: string }) {
    page.value = params?.page ?? page.value
    pageSize.value = params?.pageSize ?? pageSize.value
    keyword.value = params?.keyword ?? keyword.value
    loading.value = true
    error.value = ''
    try {
      const result = await roleService.list({ page: page.value, pageSize: pageSize.value, keyword: keyword.value })
      list.value = result.list
      total.value = result.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function createRole(data: CreateRoleData) {
    await roleService.create(data)
    await refresh()
  }

  async function updateRole(id: number, data: UpdateRoleData) {
    await roleService.update(id, data)
    await refresh()
  }

  async function removeRole(id: number) {
    await roleService.remove(id)
    await refresh()
  }

  async function assignPermissions(id: number, permissionCodes: string[]) {
    await roleService.assignPermissions(id, permissionCodes)
    await refresh()
  }

  async function refresh() {
    await Promise.all([fetchAll(), fetchList()])
  }

  return {
    roles,
    list,
    total,
    page,
    pageSize,
    keyword,
    loading,
    error,
    fetchAll,
    fetchList,
    createRole,
    updateRole,
    removeRole,
    assignPermissions,
  }
})
