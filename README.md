# 辰光 Vue 前端框架

基于 **Vue3 + TypeScript + Vite + Pinia + Vue Router** 的前端工程化分层框架，内置本地 mock 接口，前端无需后端即可独立开发与测试。当前已落地完整的 **RBAC 权限管理模块**（登录 + 后台布局 + 工作台 + 用户 / 角色 / 权限管理 + 403 + 菜单 / 按钮 / 路由三级权限控制）。

## 分层结构

```
src/
├── apis/           # 封装 axios 异步请求（http 实例 + 各模块接口）
├── services/       # 业务逻辑层（业务校验、数据加工）
├── router/         # 路由 + meta.permission + 全局守卫
├── store/          # Pinia 状态仓库（auth / permission / user / role / permission-catalog）
├── composables/    # 组合式函数（usePermission / useToast）
├── directives/     # 自定义指令（v-permission）
├── layouts/        # 后台整体布局（AdminLayout）
├── pages/          # 页面组件（路由级）
├── components/     # 公共组件与 UI 基础组件
├── types/          # 全局类型定义
└── assets/         # 设计令牌与静态资源
mock/               # 内存 mock 数据库、种子数据与可独立测试的请求处理器
docs/spec/          # RBAC PRD
docs/superpowers/   # 实现计划
docs/tests/rbac/    # RBAC 测试报告
tests/api/          # API 全接口测试（node:test）
tests/ui/           # UI 关键路径测试（Playwright）
```

## 数据流

```
pages → store → services → apis → axios → mock（/api/*）
```

## 快速开始

```bash
npm install
npm run dev        # http://localhost:5174
npm run typecheck  # TypeScript 类型检查
npm run build      # 生产构建
npm run test:api   # API 全接口测试（Node 内置测试运行器）
npm run test:ui    # UI 关键路径测试（Playwright，自动启动 dev server）
```

## 演示账号

密码统一 `123456`，登录页与顶栏身份切换器通用：

| 账号 | 角色 | 权限概要 |
|---|---|---|
| `admin` | 超级管理员 | 全部 22 项权限（superuser 直接放行） |
| `ops` | 运营管理员 | 用户 / 角色的读与增改；权限只读 |
| `viewer` | 只读观察者 | 用户 / 角色 / 权限只读 |

## Mock 接口

统一前缀 `/api`，响应 `{ code, message, data }`；鉴权分「开放 / 登录 / 权限码」三档。

| 方法 | 路径 | 所需权限 |
|---|---|---|
| GET | `/api/auth/captcha` | 开放 |
| POST | `/api/auth/login` | 开放 |
| GET | `/api/users/me` | 登录 |
| GET | `/api/users/me/permissions` | 登录 |
| GET | `/api/users` | 登录（分配角色弹窗） |
| GET | `/api/users/search` | `user:list` |
| GET | `/api/users/{id}` | `user:read` |
| POST | `/api/users` | `user:create` |
| DELETE | `/api/users/{id}` | `user:delete` |
| PUT | `/api/users/{id}/roles` | `user:assign_roles` |
| GET | `/api/users/{id}/roles` | `user:read_roles` |
| GET | `/api/roles/` | 登录（分配弹窗 / 矩阵） |
| GET | `/api/roles/search` | `role:list` |
| GET | `/api/roles/{id}` | `role:read` |
| POST | `/api/roles` | `role:create` |
| PUT | `/api/roles/{id}` | `role:update` |
| DELETE | `/api/roles/{id}` | `role:delete` |
| PUT | `/api/roles/{id}/permissions` | `role:assign_permissions` |
| GET | `/api/permissions/` | 登录（分配弹窗 / 矩阵） |
| GET | `/api/permissions/search` | `permission:list` |
| GET | `/api/permissions/{id}` | `permission:read` |
| POST | `/api/permissions` | `permission:create` |
| PUT | `/api/permissions/{id}` | `permission:update` |
| DELETE | `/api/permissions/{id}` | `permission:delete` |
| GET | `/api/dashboard/summary` | 登录 |

## 文档

- 需求：`docs/spec/rbac-prd.md`
- 实现计划：`docs/superpowers/plans/2026-11-05-rbac-module.md`
- 测试报告：`docs/tests/rbac/rbac-test-report.md`
