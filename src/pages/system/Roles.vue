<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoleStore } from '@/store/role'
import { usePermission } from '@/composables/usePermission'
import { useToast } from '@/composables/useToast'
import { permissionService } from '@/services/permission.service'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import BasePagination from '@/components/ui/BasePagination.vue'
import BaseSkeleton from '@/components/ui/BaseSkeleton.vue'
import type { Permission, PermissionModule, Role } from '@/types'

const MODULE_LABEL: Record<PermissionModule, string> = {
  user: '用户',
  role: '角色',
  permission: '权限',
  system: '系统',
}
const MODULE_ORDER: PermissionModule[] = ['user', 'role', 'permission', 'system']

const roleStore = useRoleStore()
const { hasPerm } = usePermission()
const { toast } = useToast()

const permissions = ref<Permission[]>([])
const keywordInput = ref('')

const groupedPermissions = computed(() =>
  MODULE_ORDER.map((module) => ({
    module,
    label: MODULE_LABEL[module],
    items: permissions.value.filter((permission) => permission.module === module),
  })),
)

// 创建 / 编辑
const formOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ code: '', name: '', description: '', permissionCodes: [] as string[] })

// 分配权限
const assignOpen = ref(false)
const assigning = ref(false)
const assignTarget = ref<Role | null>(null)
const assignCodes = ref<string[]>([])

// 删除
const deleteOpen = ref(false)
const deleting = ref(false)
const deleteTarget = ref<Role | null>(null)

function toggleIn(arr: string[] | number[], code: string | number) {
  const index = arr.indexOf(code as never)
  if (index === -1) arr.push(code as never)
  else arr.splice(index, 1)
}

function openCreate() {
  editingId.value = null
  form.code = ''
  form.name = ''
  form.description = ''
  form.permissionCodes = []
  formError.value = ''
  formOpen.value = true
}

function openEdit(role: Role) {
  editingId.value = role.id
  form.code = role.code
  form.name = role.name
  form.description = role.description
  form.permissionCodes = [...role.permissionCodes]
  formError.value = ''
  formOpen.value = true
}

async function submitForm() {
  formError.value = ''
  saving.value = true
  try {
    if (editingId.value === null) {
      await roleStore.createRole({
        code: form.code,
        name: form.name,
        description: form.description,
        permissionCodes: [...form.permissionCodes],
      })
      toast('success', '角色创建成功')
    } else {
      await roleStore.updateRole(editingId.value, {
        code: form.code,
        name: form.name,
        description: form.description,
      })
      toast('success', '角色已更新')
    }
    formOpen.value = false
  } catch (e) {
    formError.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

function openAssign(role: Role) {
  assignTarget.value = role
  assignCodes.value = [...role.permissionCodes]
  assignOpen.value = true
}

async function submitAssign() {
  if (!assignTarget.value) return
  assigning.value = true
  try {
    await roleStore.assignPermissions(assignTarget.value.id, [...assignCodes.value])
    toast('success', '权限分配成功')
    assignOpen.value = false
  } catch (e) {
    toast('error', e instanceof Error ? e.message : '分配失败')
  } finally {
    assigning.value = false
  }
}

function openDelete(role: Role) {
  deleteTarget.value = role
  deleteOpen.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await roleStore.removeRole(deleteTarget.value.id)
    toast('success', '角色已删除')
    deleteOpen.value = false
  } catch (e) {
    toast('error', e instanceof Error ? e.message : '删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  roleStore.fetchList()
  try {
    permissions.value = await permissionService.listAll()
  } catch {
    permissions.value = []
  }
})
</script>

<template>
  <div class="page">
    <header class="page__head">
      <div>
        <h1 class="page__title">角色管理</h1>
        <p class="page__subtitle">维护角色与权限授权关系</p>
      </div>
      <BaseButton v-if="hasPerm('role:create')" @click="openCreate">创建角色</BaseButton>
    </header>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title">角色列表（共 {{ roleStore.total }} 条）</h2>
        <div class="toolbar">
          <BaseInput v-model="keywordInput" placeholder="搜索角色码 / 名称" @keyup.enter="roleStore.fetchList({ page: 1, keyword: keywordInput })" />
          <BaseButton variant="ghost" @click="roleStore.fetchList({ page: 1, keyword: keywordInput })">搜索</BaseButton>
        </div>
      </div>

      <BaseSkeleton v-if="roleStore.loading" :rows="6" />
      <div v-else-if="roleStore.error" class="error-state">{{ roleStore.error }}</div>
      <template v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>角色码</th>
                <th>名称</th>
                <th>描述</th>
                <th>内置</th>
                <th>权限数</th>
                <th v-if="hasPerm('role:update') || hasPerm('role:assign_permissions') || hasPerm('role:delete')" class="table__actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="role in roleStore.list" :key="role.id">
                <td class="mono">{{ role.id }}</td>
                <td><code class="mono">{{ role.code }}</code></td>
                <td>{{ role.name }}</td>
                <td class="desc">{{ role.description }}</td>
                <td>
                  <BaseBadge v-if="role.isSystem" tone="dawn" text="内置" />
                  <span v-else class="muted">—</span>
                </td>
                <td class="mono">{{ role.permissionCodes.length }}</td>
                <td v-if="hasPerm('role:update') || hasPerm('role:assign_permissions') || hasPerm('role:delete')" class="table__actions">
                  <template v-if="!role.isSystem">
                    <button v-if="hasPerm('role:update')" class="link-btn" type="button" @click="openEdit(role)">编辑</button>
                    <button v-if="hasPerm('role:assign_permissions')" class="link-btn" type="button" @click="openAssign(role)">分配权限</button>
                    <button v-if="hasPerm('role:delete')" class="link-btn link-btn--danger" type="button" @click="openDelete(role)">删除</button>
                  </template>
                  <span v-else class="muted">—</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="roleStore.list.length === 0" class="empty">暂无角色</div>
        </div>
        <BasePagination
          :page="roleStore.page"
          :page-size="roleStore.pageSize"
          :total="roleStore.total"
          @change="roleStore.fetchList({ page: $event })"
        />
      </template>
    </section>

    <!-- 创建 / 编辑 -->
    <BaseModal :open="formOpen" :title="editingId === null ? '创建角色' : '编辑角色'" @close="formOpen = false">
      <form class="form" @submit.prevent="submitForm">
        <BaseInput v-model="form.code" label="角色码" placeholder="如 auditor" />
        <BaseInput v-model="form.name" label="名称" placeholder="如 审计员" />
        <BaseInput v-model="form.description" label="描述" placeholder="角色职责说明" />
        <template v-if="editingId === null">
          <div class="field">
            <span class="field__label">权限</span>
            <div class="perm-groups">
              <div v-for="group in groupedPermissions" :key="group.module" class="perm-group">
                <span class="perm-group__label">{{ group.label }}</span>
                <div class="checks">
                  <label v-for="permission in group.items" :key="permission.id" class="check">
                    <input type="checkbox" :checked="form.permissionCodes.includes(permission.code)" @change="toggleIn(form.permissionCodes, permission.code)" />
                    <span class="mono">{{ permission.code }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </template>
        <p v-if="formError" class="form-error">{{ formError }}</p>
      </form>
      <template #footer>
        <BaseButton variant="ghost" @click="formOpen = false">取消</BaseButton>
        <BaseButton :loading="saving" @click="submitForm">保存</BaseButton>
      </template>
    </BaseModal>

    <!-- 分配权限 -->
    <BaseModal :open="assignOpen" :title="`分配权限 · ${assignTarget?.name ?? ''}`" @close="assignOpen = false">
      <div class="perm-groups">
        <div v-for="group in groupedPermissions" :key="group.module" class="perm-group">
          <span class="perm-group__label">{{ group.label }}</span>
          <div class="checks">
            <label v-for="permission in group.items" :key="permission.id" class="check">
              <input type="checkbox" :checked="assignCodes.includes(permission.code)" @change="toggleIn(assignCodes, permission.code)" />
              <span class="mono">{{ permission.code }}</span>
            </label>
          </div>
        </div>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="assignOpen = false">取消</BaseButton>
        <BaseButton :loading="assigning" @click="submitAssign">保存</BaseButton>
      </template>
    </BaseModal>

    <!-- 删除确认 -->
    <BaseModal :open="deleteOpen" :title="'删除角色'" @close="deleteOpen = false">
      <p class="confirm-text">确定删除角色 <strong>{{ deleteTarget?.name }}</strong> 吗？该操作不可撤销。</p>
      <template #footer>
        <BaseButton variant="ghost" @click="deleteOpen = false">取消</BaseButton>
        <BaseButton variant="danger" :loading="deleting" @click="confirmDelete">删除</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
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
.desc {
  max-width: 260px;
  color: var(--ink-2);
}
.muted {
  color: var(--ink-3);
}
.table__actions {
  width: 210px;
  text-align: right;
  white-space: nowrap;
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
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-error {
  color: var(--danger);
  font-size: 12.5px;
}
.perm-groups {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 300px;
  overflow: auto;
}
.perm-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.perm-group__label {
  font-size: 12px;
  color: var(--ink-2);
  font-weight: 600;
}
.checks {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
}
.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  cursor: pointer;
}
.check input {
  accent-color: var(--brand);
}
.confirm-text {
  font-size: 13px;
  color: var(--ink-2);
  line-height: 1.7;
}
</style>
