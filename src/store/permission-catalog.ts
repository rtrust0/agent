import { defineStore } from 'pinia'
import { ref } from 'vue'
import { permissionService } from '@/services/permission.service'
import type { CreatePermissionData, UpdatePermissionData } from '@/apis/permission'
import type { Permission } from '@/types'

/**
 * 权限「目录」CRUD 仓库：管理权限条目的列表、搜索与增删改。
 * 与 store/permission.ts（当前用户权限码集合）职责不同，命名以 Catalog 区分。
 */
export const usePermissionCatalogStore = defineStore('permissionCatalog', () => {
  const list = ref<Permission[]>([])
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
      const result = await permissionService.list({
        page: page.value,
        pageSize: pageSize.value,
        keyword: keyword.value,
      })
      list.value = result.list
      total.value = result.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function createPermission(data: CreatePermissionData) {
    await permissionService.create(data)
    await fetchList()
  }

  async function updatePermission(id: number, data: UpdatePermissionData) {
    await permissionService.update(id, data)
    await fetchList()
  }

  async function removePermission(id: number) {
    await permissionService.remove(id)
    await fetchList()
  }

  return { list, total, page, pageSize, keyword, loading, error, fetchList, createPermission, updatePermission, removePermission }
})
