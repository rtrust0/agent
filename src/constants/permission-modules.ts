import type { Permission } from '@/types'

/**
 * 权限模块展示：模块由后端权限码前缀派生（V3 共 15 个模块），
 * 前端不再硬编码模块枚举，按后端返回顺序动态分组。
 */

export const MODULE_LABELS: Record<string, string> = {
  user: '用户',
  role: '角色',
  permission: '权限',
  data_scope: '数据范围',
  approval: '权限申请',
  system: '系统',
  dashboard: '工作台',
  agent: 'Agent',
  model: '模型',
  prompt: 'Prompt',
  knowledge: '知识库',
  tool: '工具',
  conversation: '对话日志',
  analytics: '数据统计',
}

/** 模块中文名，未知模块回退为模块前缀本身 */
export function moduleLabel(module: string): string {
  return MODULE_LABELS[module] ?? module
}

export interface PermissionGroup {
  module: string
  label: string
  items: Permission[]
}

/** 按后端顺序分组（后端权限列表按目录顺序返回，组内顺序保持不变） */
export function groupPermissions(permissions: Permission[]): PermissionGroup[] {
  const groups = new Map<string, Permission[]>()
  for (const permission of permissions) {
    const bucket = groups.get(permission.module) ?? []
    bucket.push(permission)
    groups.set(permission.module, bucket)
  }
  return [...groups.entries()].map(([module, items]) => ({
    module,
    label: moduleLabel(module),
    items,
  }))
}
