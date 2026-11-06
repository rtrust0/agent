<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useUserStore } from '@/store/user'
import { useRoleStore } from '@/store/role'
import { usePermission } from '@/composables/usePermission'
import { useToast } from '@/composables/useToast'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import BasePagination from '@/components/ui/BasePagination.vue'
import BaseSkeleton from '@/components/ui/BaseSkeleton.vue'
import type { User } from '@/types'

const userStore = useUserStore()
const roleStore = useRoleStore()
const { hasPerm } = usePermission()
const { toast } = useToast()

const keywordInput = ref('')

const addOpen = ref(false)
const adding = ref(false)
const addError = ref('')
const addForm = reactive({ username: '', email: '', password: '', roleIds: [] as number[] })

const assignOpen = ref(false)
const assigning = ref(false)
const assignTarget = ref<User | null>(null)
const assignRoleIds = ref<number[]>([])

const deleteOpen = ref(false)
const deleting = ref(false)
const deleteTarget = ref<User | null>(null)

function roleNames(roleIds: number[]): string {
  return roleIds
    .map((id) => roleStore.roles.find((role) => role.id === id)?.name)
    .filter((name): name is string => Boolean(name))
    .join('、')
}

function toggleIn(arr: number[], id: number) {
  const index = arr.indexOf(id)
  if (index === -1) arr.push(id)
  else arr.splice(index, 1)
}

function openAdd() {
  addForm.username = ''
  addForm.email = ''
  addForm.password = ''
  addForm.roleIds = []
  addError.value = ''
  addOpen.value = true
}

async function submitAdd() {
  addError.value = ''
  adding.value = true
  try {
    await userStore.createUser({
      username: addForm.username,
      email: addForm.email,
      password: addForm.password,
      roleIds: [...addForm.roleIds],
    })
    toast('success', '用户创建成功')
    addOpen.value = false
  } catch (e) {
    addError.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    adding.value = false
  }
}

function openAssign(user: User) {
  assignTarget.value = user
  assignRoleIds.value = [...user.roleIds]
  assignOpen.value = true
}

async function submitAssign() {
  if (!assignTarget.value) return
  assigning.value = true
  try {
    await userStore.assignRoles(assignTarget.value.id, [...assignRoleIds.value])
    toast('success', '角色分配成功')
    assignOpen.value = false
  } catch (e) {
    toast('error', e instanceof Error ? e.message : '分配失败')
  } finally {
    assigning.value = false
  }
}

function openDelete(user: User) {
  deleteTarget.value = user
  deleteOpen.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await userStore.removeUser(deleteTarget.value.id)
    toast('success', '用户已删除')
    deleteOpen.value = false
  } catch (e) {
    toast('error', e instanceof Error ? e.message : '删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  userStore.fetchList()
  roleStore.fetchAll()
})
</script>

<template>
  <div class="page">
    <header class="page__head">
      <div>
        <h1 class="page__title">用户管理</h1>
        <p class="page__subtitle">管理平台账号与角色分配</p>
      </div>
      <BaseButton v-if="hasPerm('user:create')" @click="openAdd">添加用户</BaseButton>
    </header>

    <section class="panel">
      <div class="panel__head">
        <h2 class="panel__title">用户列表（共 {{ userStore.total }} 条）</h2>
        <div class="toolbar">
          <BaseInput v-model="keywordInput" placeholder="搜索用户名 / 邮箱" @keyup.enter="userStore.fetchList({ page: 1, keyword: keywordInput })" />
          <BaseButton variant="ghost" @click="userStore.fetchList({ page: 1, keyword: keywordInput })">搜索</BaseButton>
        </div>
      </div>

      <BaseSkeleton v-if="userStore.loading" :rows="6" />
      <div v-else-if="userStore.error" class="error-state">{{ userStore.error }}</div>
      <template v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>状态</th>
                <th>创建时间</th>
                <th v-if="hasPerm('user:assign_roles') || hasPerm('user:delete')" class="table__actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in userStore.list" :key="user.id">
                <td class="mono">{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.email }}</td>
                <td>{{ roleNames(user.roleIds) || '—' }}</td>
                <td>
                  <BaseBadge :tone="user.isActive ? 'grant' : 'danger'" :text="user.isActive ? '启用' : '停用'" />
                </td>
                <td class="mono">{{ user.createdAt }}</td>
                <td v-if="hasPerm('user:assign_roles') || hasPerm('user:delete')" class="table__actions">
                  <button v-if="hasPerm('user:assign_roles')" class="link-btn" type="button" @click="openAssign(user)">分配角色</button>
                  <button v-if="hasPerm('user:delete')" class="link-btn link-btn--danger" type="button" @click="openDelete(user)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="userStore.list.length === 0" class="empty">暂无用户</div>
        </div>
        <BasePagination
          :page="userStore.page"
          :page-size="userStore.pageSize"
          :total="userStore.total"
          @change="userStore.fetchList({ page: $event })"
        />
      </template>
    </section>

    <!-- 添加用户 -->
    <BaseModal :open="addOpen" :title="'添加用户'" @close="addOpen = false">
      <form class="form" @submit.prevent="submitAdd">
        <BaseInput v-model="addForm.username" label="用户名" placeholder="请输入用户名" />
        <BaseInput v-model="addForm.email" label="邮箱" type="email" placeholder="请输入邮箱" />
        <BaseInput v-model="addForm.password" label="密码" type="password" placeholder="请输入密码" />
        <div class="field">
          <span class="field__label">初始角色</span>
          <div class="checks">
            <label v-for="role in roleStore.roles" :key="role.id" class="check">
              <input type="checkbox" :checked="addForm.roleIds.includes(role.id)" @change="toggleIn(addForm.roleIds, role.id)" />
              <span>{{ role.name }}</span>
            </label>
          </div>
        </div>
        <p v-if="addError" class="form-error">{{ addError }}</p>
      </form>
      <template #footer>
        <BaseButton variant="ghost" @click="addOpen = false">取消</BaseButton>
        <BaseButton :loading="adding" @click="submitAdd">创建</BaseButton>
      </template>
    </BaseModal>

    <!-- 分配角色 -->
    <BaseModal :open="assignOpen" :title="`分配角色 · ${assignTarget?.username ?? ''}`" @close="assignOpen = false">
      <div class="field">
        <span class="field__label">角色</span>
        <div class="checks">
          <label v-for="role in roleStore.roles" :key="role.id" class="check">
            <input type="checkbox" :checked="assignRoleIds.includes(role.id)" @change="toggleIn(assignRoleIds, role.id)" />
            <span>{{ role.name }}</span>
          </label>
        </div>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="assignOpen = false">取消</BaseButton>
        <BaseButton :loading="assigning" @click="submitAssign">保存</BaseButton>
      </template>
    </BaseModal>

    <!-- 删除确认 -->
    <BaseModal :open="deleteOpen" :title="'删除用户'" @close="deleteOpen = false">
      <p class="confirm-text">确定删除用户 <strong>{{ deleteTarget?.username }}</strong> 吗？该操作不可撤销。</p>
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
  color: var(--ink-2);
}
.table__actions {
  width: 160px;
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
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-error {
  color: var(--danger);
  font-size: 12.5px;
}
.checks {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
}
.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--ink);
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
