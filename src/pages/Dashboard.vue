<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { dashboardService } from '@/services/dashboard.service'
import { roleService } from '@/services/role.service'
import { permissionService } from '@/services/permission.service'
import { authService } from '@/services/auth.service'
import BaseSkeleton from '@/components/ui/BaseSkeleton.vue'
import type { DashboardSummary, Permission, PermissionModule, Role } from '@/types'

const MODULE_LABEL: Record<PermissionModule, string> = {
  user: '用户',
  role: '角色',
  permission: '权限',
  system: '系统',
}

const summary = ref<DashboardSummary | null>(null)
const myPermissions = ref<string[]>([])
const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const loading = ref(true)
const error = ref('')

const statCards = computed(() => [
  { key: 'totalUsers', label: '用户数', value: summary.value?.totalUsers ?? 0 },
  { key: 'totalRoles', label: '角色数', value: summary.value?.totalRoles ?? 0 },
  { key: 'totalPermissions', label: '权限数', value: summary.value?.totalPermissions ?? 0 },
])

const groupedPermissions = computed(() => {
  const groups = new Map<PermissionModule, string[]>()
  const codeToModule = new Map(permissions.value.map((p) => [p.code, p.module]))
  for (const code of myPermissions.value) {
    const module = codeToModule.get(code)
    if (!module) continue
    const list = groups.get(module) ?? []
    list.push(code)
    groups.set(module, list)
  }
  return [...groups.entries()].map(([module, codes]) => ({ module, label: MODULE_LABEL[module], codes }))
})

const matrixRows = computed(() =>
  permissions.value.map((permission) => ({
    ...permission,
    grants: roles.value.map((role) => role.permissionCodes.includes(permission.code)),
  })),
)

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const [summaryData, perms, roleList, permissionList] = await Promise.all([
      dashboardService.summary(),
      authService.mePermissions(),
      roleService.listAll(),
      permissionService.listAll(),
    ])
    summary.value = summaryData
    myPermissions.value = perms
    roles.value = roleList
    permissions.value = permissionList
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <header class="page__head">
      <div>
        <h1 class="page__title">工作台</h1>
        <p class="page__subtitle">RBAC 权限概览 · 当前身份可见范围与授权矩阵</p>
      </div>
    </header>

    <BaseSkeleton v-if="loading" :rows="8" />
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <template v-else>
      <section class="stats">
        <article v-for="card in statCards" :key="card.key" class="stat">
          <span class="stat__label">{{ card.label }}</span>
          <span class="stat__value">{{ card.value }}</span>
        </article>
      </section>

      <section class="panel">
        <div class="panel__head">
          <h2 class="panel__title">当前身份权限（{{ myPermissions.length }} 项）</h2>
        </div>
        <div class="panel__body">
          <div v-if="groupedPermissions.length === 0" class="empty">当前身份无任何权限</div>
          <div v-for="group in groupedPermissions" :key="group.module" class="perm-group">
            <span class="perm-group__label">{{ group.label }}</span>
            <div class="perm-group__codes">
              <code v-for="code in group.codes" :key="code" class="perm-chip">{{ code }}</code>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel__head">
          <h2 class="panel__title">权限矩阵预览</h2>
          <span class="panel__hint">行 = 权限，列 = 角色，实心 = 已授权</span>
        </div>
        <div class="panel__body panel__body--flush">
          <div class="matrix-scroll">
            <table class="matrix">
              <thead>
                <tr>
                  <th class="matrix__code-col">权限码</th>
                  <th v-for="role in roles" :key="role.id">{{ role.name }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in matrixRows" :key="row.code">
                  <td class="matrix__code-col"><code>{{ row.code }}</code></td>
                  <td v-for="(grant, index) in row.grants" :key="index" class="matrix__cell">
                    <span class="matrix__dot" :class="{ 'matrix__dot--on': grant }" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.stat__label {
  font-size: 12.5px;
  color: var(--ink-2);
}
.stat__value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.03em;
  font-family: var(--font-mono);
}
.panel {
  margin-bottom: 18px;
}
.panel__hint {
  font-size: 12px;
  color: var(--ink-3);
}
.panel__body--flush {
  padding: 0;
}
.perm-group {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 8px 0;
  border-bottom: 1px solid #f1f3f6;
}
.perm-group:last-child {
  border-bottom: none;
}
.perm-group__label {
  min-width: 42px;
  padding-top: 2px;
  font-size: 12.5px;
  color: var(--ink-2);
}
.perm-group__codes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.perm-chip {
  padding: 3px 8px;
  border-radius: 5px;
  background: var(--brand-weak);
  color: var(--brand);
  font-size: 11.5px;
}
.matrix-scroll {
  overflow: auto;
  max-height: 420px;
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
  z-index: 1;
  background: var(--navy-900);
  color: #fff;
  font-weight: 500;
}
.matrix__code-col {
  text-align: left;
  font-family: var(--font-mono);
  color: var(--ink-2);
}
.matrix__dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 1.5px solid var(--line);
  border-radius: 3px;
}
.matrix__dot--on {
  border-color: var(--grant);
  background: var(--grant);
}
@media (max-width: 768px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
