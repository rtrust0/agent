<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { usePermissionCatalogStore } from '@/store/permission-catalog'
import { useRoleStore } from '@/store/role'
import { usePermission } from '@/composables/usePermission'
import { useToast } from '@/composables/useToast'
import { permissionService } from '@/services/permission.service'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseSelect from '@/components/ui/BaseSelect.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BasePagination from '@/components/ui/BasePagination.vue'
import BaseSkeleton from '@/components/ui/BaseSkeleton.vue'
import type { Permission, PermissionModule } from '@/types'

const MODULE_LABEL: Record<PermissionModule, string> = {
  user: '用户',
  role: '角色',
  permission: '权限',
  system: '系统',
}
const MODULE_ORDER: PermissionModule[] = ['user', 'role', 'permission', 'system']
const MODULE_OPTIONS = MODULE_ORDER.map((module) => ({ label: MODULE_LABEL[module], value: module }))

const catalog = usePermissionCatalogStore()
const roleStore = useRoleStore()
const { hasPerm } = usePermission()
const { toast } = useToast()

const view = ref<'list' | 'matrix'>('list')
const keywordInput = ref('')
const allPermissions = ref<Permission[]>([])

const matrixGroups = computed(() =>
  MODULE_ORDER.map((module) => ({
    module,
    label: MODULE_LABEL[module],
    rows: allPermissions.value
      .filter((permission) => permission.module === module)
      .map((permission) => ({
        ...permission,
        grants: roleStore.roles.map((role) => role.permissionCodes.includes(permission.code)),
      })),
  })),
)

// 创建 / 编辑
const formOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ code: '', name: '', module: 'user' as PermissionModule })

// 删除
const deleteOpen = ref(false)
const deleting = ref(false)
const deleteTarget = ref<Permission | null>(null)

function openCreate() {
  editingId.value = null
  form.code = ''
  form.name = ''
  form.module = 'user'
  formError.value = ''
  formOpen.value = true
}

function openEdit(permission: Permission) {
  editingId.value = permission.id
  form.code = permission.code
  form.name = permission.name
  form.module = permission.module
  formError.value = ''
  formOpen.value = true
}

async function submitForm() {
  formError.value = ''
  saving.value = true
  try {
    if (editingId.value === null) {
      await catalog.createPermission({ code: form.code, name: form.name, module: form.module })
      toast('success', '权限创建成功')
    } else {
      await catalog.updatePermission(editingId.value, { name: form.name, module: form.module })
      toast('success', '权限已更新')
    }
    await refreshMatrix()
    formOpen.value = false
  } catch (e) {
    formError.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

function openDelete(permission: Permission) {
  deleteTarget.value = permission
  deleteOpen.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await catalog.removePermission(deleteTarget.value.id)
    toast('success', '权限已删除')
    await refreshMatrix()
    deleteOpen.value = false
  } catch (e) {
    toast('error', e instanceof Error ? e.message : '删除失败')
  } finally {
    deleting.value = false
  }
}

async function refreshMatrix() {
  try {
    allPermissions.value = await permissionService.listAll()
  } catch {
    allPermissions.value = []
  }
}

onMounted(async () => {
  catalog.fetchList()
  roleStore.fetchAll()
  await refreshMatrix()
})
</script>

<template>
  <div class="page">
    <header class="page__head">
      <div>
        <h1 class="page__title">权限管理</h1>
        <p class="page__subtitle">维护权限码目录，并以矩阵查看角色授权关系</p>
      </div>
      <div class="head-actions">
        <div class="segmented">
          <button class="segmented__btn" :class="{ 'segmented__btn--active': view === 'list' }" type="button" @click="view = 'list'">列表</button>
          <button class="segmented__btn" :class="{ 'segmented__btn--active': view === 'matrix' }" type="button" @click="view = 'matrix'">矩阵</button>
        </div>
        <BaseButton v-if="view === 'list' && hasPerm('permission:create')" @click="openCreate">创建权限</BaseButton>
      </div>
    </header>

    <!-- 列表视图 -->
    <section v-if="view === 'list'" class="panel">
      <div class="panel__head">
        <h2 class="panel__title">权限列表（共 {{ catalog.total }} 条）</h2>
        <div class="toolbar">
          <BaseInput v-model="keywordInput" placeholder="搜索权限码 / 名称" @keyup.enter="catalog.fetchList({ page: 1, keyword: keywordInput })" />
          <BaseButton variant="ghost" @click="catalog.fetchList({ page: 1, keyword: keywordInput })">搜索</BaseButton>
        </div>
      </div>

      <BaseSkeleton v-if="catalog.loading" :rows="6" />
      <div v-else-if="catalog.error" class="error-state">{{ catalog.error }}</div>
      <template v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>权限码</th>
                <th>名称</th>
                <th>模块</th>
                <th v-if="hasPerm('permission:update') || hasPerm('permission:delete')" class="table__actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="permission in catalog.list" :key="permission.id">
                <td class="mono">{{ permission.id }}</td>
                <td><code class="mono">{{ permission.code }}</code></td>
                <td>{{ permission.name }}</td>
                <td>{{ MODULE_LABEL[permission.module] }}</td>
                <td v-if="hasPerm('permission:update') || hasPerm('permission:delete')" class="table__actions">
                  <button v-if="hasPerm('permission:update')" class="link-btn" type="button" @click="openEdit(permission)">编辑</button>
                  <button v-if="hasPerm('permission:delete')" class="link-btn link-btn--danger" type="button" @click="openDelete(permission)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="catalog.list.length === 0" class="empty">暂无权限</div>
        </div>
        <BasePagination
          :page="catalog.page"
          :page-size="catalog.pageSize"
          :total="catalog.total"
          @change="catalog.fetchList({ page: $event })"
        />
      </template>
    </section>

    <!-- 矩阵视图 -->
    <section v-else class="panel">
      <div class="panel__head">
        <h2 class="panel__title">权限矩阵</h2>
        <span class="panel__hint">行 = 权限，列 = 角色；绿色实心 = 已授权</span>
      </div>
      <div class="matrix-scroll">
        <table class="matrix">
          <thead>
            <tr>
              <th class="matrix__code">权限码</th>
              <th v-for="role in roleStore.roles" :key="role.id">{{ role.name }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="group in matrixGroups" :key="group.module">
              <tr class="matrix__module-row">
                <td :colspan="roleStore.roles.length + 1">{{ group.label }}</td>
              </tr>
              <tr v-for="row in group.rows" :key="row.code">
                <td class="matrix__code">
                  <code>{{ row.code }}</code>
                  <span class="matrix__name">{{ row.name }}</span>
                </td>
                <td v-for="(grant, index) in row.grants" :key="index" class="matrix__cell">
                  <span class="matrix__dot" :class="{ 'matrix__dot--on': grant }" />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 创建 / 编辑 -->
    <BaseModal :open="formOpen" :title="editingId === null ? '创建权限' : '编辑权限'" @close="formOpen = false">
      <form class="form" @submit.prevent="submitForm">
        <BaseInput v-model="form.code" label="权限码" placeholder="如 user:export" :disabled="editingId !== null" />
        <BaseInput v-model="form.name" label="名称" placeholder="如 导出用户" />
        <BaseSelect v-model="form.module" label="模块" :options="MODULE_OPTIONS" />
        <p v-if="formError" class="form-error">{{ formError }}</p>
      </form>
      <template #footer>
        <BaseButton variant="ghost" @click="formOpen = false">取消</BaseButton>
        <BaseButton :loading="saving" @click="submitForm">保存</BaseButton>
      </template>
    </BaseModal>

    <!-- 删除确认 -->
    <BaseModal :open="deleteOpen" :title="'删除权限'" @close="deleteOpen = false">
      <p class="confirm-text">确定删除权限 <strong>{{ deleteTarget?.code }}</strong> 吗？被角色引用的权限不可删除。</p>
      <template #footer>
        <BaseButton variant="ghost" @click="deleteOpen = false">取消</BaseButton>
        <BaseButton variant="danger" :loading="deleting" @click="confirmDelete">删除</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.segmented {
  display: flex;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f3f5f8;
}
.segmented__btn {
  height: 28px;
  padding: 0 14px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ink-2);
  font-size: 12.5px;
}
.segmented__btn--active {
  background: #fff;
  color: var(--navy-900);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar :deep(.field__input) {
  width: 220px;
}
.table-wrap {
  overflow-x: auto;
}
.mono {
  font-family: var(--font-mono);
  font-size: 12.5px;
}
.table__actions {
  width: 130px;
  text-align: right;
}
.link-btn {
  border: none;
  background: transparent;
  color: var(--brand);
  font-size: 12.5px;
  padding: 0 4px;
}
.link-btn--danger {
  color: var(--danger);
}
.link-btn:hover {
  text-decoration: underline;
}
.panel__hint {
  font-size: 12px;
  color: var(--ink-3);
}
.matrix-scroll {
  overflow: auto;
  max-height: 640px;
}
.matrix {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}
.matrix th,
.matrix td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  text-align: center;
  white-space: nowrap;
}
.matrix thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--navy-900);
  color: #fff;
  font-weight: 500;
}
.matrix__module-row td {
  position: sticky;
  top: 37px;
  z-index: 1;
  background: #f3f5f8;
  color: var(--ink-2);
  font-weight: 600;
  text-align: left;
}
.matrix__code {
  text-align: left;
  font-family: var(--font-mono);
  color: var(--ink);
}
.matrix__name {
  margin-left: 8px;
  font-family: var(--font-sans);
  color: var(--ink-3);
  font-size: 12px;
}
.matrix__dot {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 1.5px solid var(--line);
  border-radius: 3px;
}
.matrix__dot--on {
  border-color: var(--grant);
  background: var(--grant);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-error {
  color: var(--danger);
  font-size: 12.5px;
}
.confirm-text {
  font-size: 13px;
  color: var(--ink-2);
  line-height: 1.7;
}
</style>
