/* 辰光 Agent 平台 · RBAC 原型 — Mock 数据
   与 PROJECT_SPEC_V2.md 的权限码规范保持一致 */
(function (global) {
  'use strict';

  // 权限清单（模块:操作）
  var PERMISSIONS = [
    { code: 'user:list', name: '查看用户列表', module: 'user' },
    { code: 'user:read', name: '查看用户详情', module: 'user' },
    { code: 'user:create', name: '创建用户', module: 'user' },
    { code: 'user:update', name: '更新用户', module: 'user' },
    { code: 'user:delete', name: '删除用户', module: 'user' },
    { code: 'user:assign_roles', name: '分配角色', module: 'user' },
    { code: 'user:read_roles', name: '查看用户角色', module: 'user' },
    { code: 'role:list', name: '查看角色列表', module: 'role' },
    { code: 'role:read', name: '查看角色详情', module: 'role' },
    { code: 'role:create', name: '创建角色', module: 'role' },
    { code: 'role:update', name: '更新角色', module: 'role' },
    { code: 'role:delete', name: '删除角色', module: 'role' },
    { code: 'role:assign_permissions', name: '分配权限', module: 'role' },
    { code: 'permission:list', name: '查看权限列表', module: 'permission' },
    { code: 'permission:read', name: '查看权限详情', module: 'permission' },
    { code: 'permission:create', name: '创建权限', module: 'permission' },
    { code: 'permission:update', name: '更新权限', module: 'permission' },
    { code: 'permission:delete', name: '删除权限', module: 'permission' },
    { code: 'system:api_keys', name: 'API 密钥管理', module: 'system' },
    { code: 'system:audit', name: '审计日志', module: 'system' },
    { code: 'system:alerts', name: '告警规则', module: 'system' },
    { code: 'system:settings', name: '系统配置', module: 'system' },
  ];

  var ALL_CODES = PERMISSIONS.map(function (p) { return p.code; });

  // 角色
  var ROLES = [
    { id: 1, code: 'super_admin', name: '超级管理员', description: '拥有平台全部权限，可管理一切资源', isSystem: true, permissions: ALL_CODES.slice() },
    { id: 2, code: 'ops_admin', name: '运营管理员', description: '负责日常运营，可增改用户与角色，不可删除或分配', isSystem: false, permissions: ['user:list', 'user:read', 'user:create', 'user:update', 'user:read_roles', 'role:list', 'role:read', 'role:create', 'role:update', 'permission:list', 'permission:read'] },
    { id: 3, code: 'viewer', name: '只读观察者', description: '只能查看用户、角色与权限，不可做任何修改', isSystem: false, permissions: ['user:list', 'user:read', 'user:read_roles', 'role:list', 'role:read', 'permission:list', 'permission:read'] },
  ];

  // 身份（用于顶栏身份切换演示）
  var IDENTITIES = [
    { key: 'super', name: '管理员', username: 'admin', email: 'admin@chenguang.ai', roleName: '超级管理员', superuser: true, permissions: ALL_CODES.slice() },
    { key: 'ops', name: '运营', username: 'ops', email: 'ops@chenguang.ai', roleName: '运营管理员', superuser: false, permissions: ROLES[1].permissions.slice() },
    { key: 'viewer', name: '观察者', username: 'viewer', email: 'viewer@chenguang.ai', roleName: '只读观察者', superuser: false, permissions: ROLES[2].permissions.slice() },
  ];

  // 用户列表
  var USERS = [
    { id: 1, username: 'admin', email: 'admin@chenguang.ai', roles: ['超级管理员'], isActive: true, createdAt: '2026-03-19 10:24' },
    { id: 2, username: 'ops', email: 'ops@chenguang.ai', roles: ['运营管理员'], isActive: true, createdAt: '2026-03-20 09:11' },
    { id: 3, username: 'viewer', email: 'viewer@chenguang.ai', roles: ['只读观察者'], isActive: true, createdAt: '2026-03-21 14:02' },
    { id: 4, username: 'zhangwei', email: 'zhangwei@chenguang.ai', roles: ['运营管理员'], isActive: true, createdAt: '2026-04-02 16:45' },
    { id: 5, username: 'liming', email: 'liming@chenguang.ai', roles: ['只读观察者'], isActive: false, createdAt: '2026-04-10 08:30' },
    { id: 6, username: 'wangfang', email: 'wangfang@chenguang.ai', roles: ['运营管理员', '只读观察者'], isActive: true, createdAt: '2026-05-06 11:20' },
  ];

  var MODULE_LABELS = {
    user: '用户',
    role: '角色',
    permission: '权限',
    system: '系统',
  };

  global.RBAC_DATA = {
    PERMISSIONS: PERMISSIONS,
    ROLES: ROLES,
    IDENTITIES: IDENTITIES,
    USERS: USERS,
    MODULE_LABELS: MODULE_LABELS,
    ALL_CODES: ALL_CODES,
  };
})(window);
