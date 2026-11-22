# 辰光 Agent 平台 — 项目说明书 V2（RBAC 授权功能增强版）

> 本版本基于 `docs/PROJECT_SPEC.md`（V1）的全部内容，新增 **RBAC 模块授权（Authorization）功能**，涵盖后端接口权限拦截与前端菜单/按钮/路由守卫的权限控制。V2 作为全新 PRD，可直接供后续开发参考。

---

## 一、项目概述

辰光 Agent 平台是一个**企业级 AI Agent 管理平台**，提供 Agent 全生命周期管理、知识库(RAG)管理、Prompt 工程、模型管理、工具编排、对话日志分析等能力。

项目采用**前后端分离**架构：
- **后端**：Python 3.13 + FastAPI（异步），位于根目录 `src/`
- **前端**：React 19 + TypeScript + Vite，位于 `app/` 目录
- **数据库**：MySQL（通过 SQLAlchemy 异步 ORM）
- **缓存**：Redis（验证码存储等）
- **数据库迁移**：Alembic

### 当前开发状态

| 层 | 状态 |
|---|---|
| 后端 — RBAC 模块（用户/角色/权限/认证/验证码） | ✅ 已实现（数据模型 + CRUD + 分配关系） |
| 后端 — RBAC 授权（接口权限拦截、当前用户权限查询） | ❌ **V2 新增，待实现** |
| 后端 — Agent/模型/Prompt/知识库/工具等业务模块 | ❌ 待实现 |
| 前端 — 全部页面 UI + Mock 数据 | ✅ 已实现 |
| 前端 — 对接真实后端 API（用户/角色/权限 CRUD） | ✅ 已完成 |
| 前端 — 菜单/按钮/路由基于权限的显示控制 | ❌ **V2 新增，待实现** |

---

## 二、RBAC 授权功能需求（V2 新增核心）

### 2.1 需求背景

现有 RBAC 模块已完善用户/角色/权限的 ORM 模型、Pydantic Schema、Repository、Service、API 层，支持：
- 用户/角色/权限的完整 CRUD
- 给用户分配角色（`PUT /users/{id}/roles`）
- 给角色分配权限（`PUT /roles/{id}/permissions`）

但**缺少授权拦截能力**：
1. 后端 `get_current_user()` 只做身份认证（JWT 校验 + 查用户），所有已登录用户均可调用用户/角色/权限等管理接口，无权限码校验；
2. 后端没有提供“当前用户拥有哪些权限”的查询接口，前端无法根据权限做 UI 控制；
3. 前端侧边栏菜单、系统管理子菜单、操作按钮（创建/编辑/删除/分配角色/权限）对所有登录用户均可见，无权限差异化；
4. 前端路由守卫 `AuthGuard` 只校验是否登录，不校验路由访问权限。

### 2.2 目标

- **后端**：基于权限码（permission code）对敏感管理接口做权限拦截，缺权限返回 403；
- **后端**：提供当前登录用户权限列表查询接口，供前端做菜单/按钮/路由控制；
- **前端**：侧边栏菜单按当前用户权限显示/隐藏；
- **前端**：操作按钮按当前用户权限显示/隐藏；
- **前端**：路由守卫扩展，无权限访问页面时被拦截并提示。

### 2.3 非目标（本次不做，后续版本再考虑）

- 资源级数据权限（本人/部门/全量数据隔离）；
- 权限操作审计日志；
- 权限申请与审批流程；
- 前端单元测试（Vitest/Jest 尚未引入）。

### 2.4 权限码设计规范

权限码格式：**`模块:操作`**，全部小写，建议清单如下：

| 模块 | 权限码 | 含义 |
|---|---|---|
| user | `user:list` | 用户列表查看 |
| user | `user:read` | 用户详情查看 |
| user | `user:create` | 创建用户 |
| user | `user:update` | 更新用户 |
| user | `user:delete` | 删除用户 |
| user | `user:assign_roles` | 给用户分配角色 |
| user | `user:read_roles` | 查看用户角色列表 |
| role | `role:list` | 角色列表查看 |
| role | `role:read` | 角色详情查看 |
| role | `role:create` | 创建角色 |
| role | `role:update` | 更新角色 |
| role | `role:delete` | 删除角色 |
| role | `role:assign_permissions` | 给角色分配权限 |
| permission | `permission:list` | 权限列表查看 |
| permission | `permission:read` | 权限详情查看 |
| permission | `permission:create` | 创建权限 |
| permission | `permission:update` | 更新权限 |
| permission | `permission:delete` | 删除权限 |
| system | `system:api_keys` | API 密钥管理 |
| system | `system:audit` | 审计日志查看 |
| system | `system:alerts` | 告警规则管理 |
| system | `system:settings` | 系统配置管理 |

**超级管理员**（`User.is_superuser == true`）拥有所有权限，权限校验时直接放行，无需逐条匹配。

### 2.5 后端需求

#### 2.5.1 新增依赖注入：带权限码的当前用户获取

在 `src/core/deps.py` 中新增依赖函数 `get_current_user_with_permission(permission_code: str)`：

1. 复用现有 `get_current_user()` 完成 JWT 校验并获取当前用户 `User` 对象（含 `roles`，`lazy="selectin"` 立即加载）；
2. 若用户 `is_superuser == true`，直接返回用户，无需校验权限码；
3. 否则遍历用户的所有角色及其关联权限，提取权限码集合；
4. 若请求的 `permission_code` 在用户权限码集合中，返回用户；
5. 若不在，抛出 `BizException(code=403, message="没有权限执行该操作")`，全局异常处理器将其返回为 HTTP 200 + 业务错误码 403。

#### 2.5.2 新增接口：当前用户权限查询

| 项目 | 内容 |
|---|---|
| 路由 | `GET /api/v1/users/me/permissions` |
| 摘要 | 获取当前登录用户拥有的所有权限码 |
| 依赖 | `get_current_user`（仅需登录，无需特定权限码）|
| 返回 | `ResponseSchema[list[str]]`，权限码字符串列表（已去重）|
| 超管行为 | 返回系统中全部已定义权限码 |

#### 2.5.3 接口权限拦截清单

下表列出需在 API 层加上 `Depends(get_current_user_with_permission("xxx"))` 的接口：

| 接口 | 方法 | 所需权限码 | 说明 |
|---|---|---|---|
| `/api/v1/users` | POST | `user:create` | 创建用户 |
| `/api/v1/users/search` | GET | `user:list` | 用户分页搜索 |
| `/api/v1/users/{id}` | GET | `user:read` | 用户详情 |
| `/api/v1/users/{id}` | DELETE | `user:delete` | 删除用户 |
| `/api/v1/users/{id}/roles` | PUT | `user:assign_roles` | 给用户分配角色 |
| `/api/v1/users/{id}/roles` | GET | `user:read_roles` | 查看用户角色 |
| `/api/v1/users/me` | GET | 无（自查） | 当前用户信息，无需额外权限 |
| `/api/v1/users/me/permissions` | GET | 无（自查） | 当前用户权限，无需额外权限 |
| `/api/v1/roles` | POST | `role:create` | 创建角色 |
| `/api/v1/roles/search` | GET | `role:list` | 角色分页搜索 |
| `/api/v1/roles/{id}` | GET | `role:read` | 角色详情 |
| `/api/v1/roles/{id}` | PUT | `role:update` | 更新角色 |
| `/api/v1/roles/{id}` | DELETE | `role:delete` | 删除角色 |
| `/api/v1/roles/{id}/permissions` | PUT | `role:assign_permissions` | 给角色分配权限 |
| `/api/v1/permissions` | POST | `permission:create` | 创建权限 |
| `/api/v1/permissions/search` | GET | `permission:list` | 权限分页搜索 |
| `/api/v1/permissions/{id}` | GET | `permission:read` | 权限详情 |
| `/api/v1/permissions/{id}` | PUT | `permission:update` | 更新权限 |
| `/api/v1/permissions/{id}` | DELETE | `permission:delete` | 删除权限 |

#### 2.5.4 错误响应约定

- 权限不足：HTTP 200，`{"code": 403, "message": "没有权限执行该操作", "data": null}`（遵循现有 `BizException` 约定）；
- 未登录 / token 过期：HTTP 401，前端 `ApiClient` 已处理自动跳转 `/login`。

#### 2.5.5 数据库模型变更

- **无需新增数据库表**，复用现有 `users`、`roles`、`permissions`、`user_roles`、`role_permissions`；
- ORM 模型不变，无需新增 Alembic 迁移；
- 建议：初始化种子数据，预置 `admin` 超级管理员角色及常用权限码，供首次部署后直接使用。

---

## 三、前端 RBAC 授权需求（V2 新增）

前端通过 `VITE_USE_MOCK` 开关在 Mock 与真实 API 之间切换，授权控制需在两种模式下都能工作。Mock 模式下可模拟返回当前用户权限码列表。

### 3.1 当前用户权限获取

- 在 `app/src/services/system.ts`（或 `app/src/services/auth.ts`）中新增 `getCurrentUserPermissions()`：
  - 真实后端：调用 `GET /api/v1/users/me/permissions`，返回 `string[]`；
  - Mock 模式：从 mock 数据中返回预设的权限码列表；
- 登录成功后及页面初始化时调用一次，将权限码集合存储在全局状态（React Context）或页面局部状态，供菜单、按钮、路由守卫消费。

### 3.2 侧边栏菜单权限过滤（`app/src/layouts/DashboardLayout.tsx`）

为 `menuItems`（平台功能）和 `systemMenuItems`（系统管理子菜单）各自关联所需权限码：

| 菜单项 | 路由 | 所需权限码 |
|---|---|---|
| 用户管理 | `/system/users` | `user:list` |
| 角色管理 | `/system/roles` | `role:list` |
| 权限管理 | `/system/permissions` | `permission:list` |
| API 密钥 | `/system/api-keys` | `system:api_keys` |
| 审计日志 | `/system/audit` | `system:audit` |
| 告警规则 | `/system/alerts` | `system:alerts` |
| 系统配置 | `/system/settings` | `system:settings` |

控制逻辑：
- 当前用户不具备菜单项所需权限时，该菜单项不渲染；
- 若“系统管理”下所有子菜单均因无权限被隐藏，则“系统管理”父菜单也不显示；
- 当前用户无任何可见菜单时，侧边栏仅保留 Logo 与用户区域。

### 3.3 操作按钮权限过滤（各 system 页面）

| 页面 | 按钮 | 所需权限码 | 文件 |
|---|---|---|---|
| 用户管理 | 添加用户 | `user:create` | `app/src/pages/system/Users.tsx` |
| 用户管理 | 删除用户（表格操作列） | `user:delete` | `app/src/pages/system/Users.tsx` |
| 用户管理 | 分配角色（表格操作列） | `user:assign_roles` | `app/src/pages/system/Users.tsx` |
| 角色管理 | 创建角色 | `role:create` | `app/src/pages/system/Roles.tsx` |
| 角色管理 | 编辑角色（表格操作列） | `role:update` | `app/src/pages/system/Roles.tsx` |
| 角色管理 | 删除角色（表格操作列） | `role:delete` | `app/src/pages/system/Roles.tsx` |
| 角色管理 | 分配权限（表格操作列） | `role:assign_permissions` | `app/src/pages/system/Roles.tsx` |
| 权限管理 | 创建权限 | `permission:create` | `app/src/pages/system/Permissions.tsx` |
| 权限管理 | 编辑权限（表格操作列） | `permission:update` | `app/src/pages/system/Permissions.tsx` |
| 权限管理 | 删除权限（表格操作列） | `permission:delete` | `app/src/pages/system/Permissions.tsx` |

控制逻辑：当前用户不具备按钮对应权限时，该按钮不渲染；表格中对应操作列整体隐藏。

### 3.4 路由守卫扩展（`app/src/components/AuthGuard.tsx`）

现有 `AuthGuard` 仅校验 `authService.isLoggedIn()`，未登录跳转 `/login`。

新增扩展：
- `AuthGuard` 接受可选的 `requiredPermission?: string` 属性；
- 若指定 `requiredPermission`，则校验当前用户权限集合是否包含该权限码；
- 无权限时：重定向到 `/login` 或展示“无权访问该页面”提示页（两种方式供选型，建议优先重定向并携带错误提示）；
- 所有 `/system/*` 路由可按需包裹带权限码的 `AuthGuard`，实现页面级访问控制。

### 3.5 前后端接口契约

| 场景 | 后端返回 | 前端处理 |
|---|---|---|
| 权限足够 | HTTP 200 + 正常业务数据 | 正常渲染页面/执行操作 |
| 权限不足 | HTTP 200 + `{"code": 403, "message": "没有权限执行该操作", "data": null}` | 捕获业务错误码 403，提示用户“无权执行该操作” |
| 未登录/Token 过期 | HTTP 401 | `ApiClient` 自动清除 token 并跳转 `/login`（已实现）|

---

## 四、验收标准

1. 以非超级管理员用户登录，调用需要权限的管理接口，后端返回业务错误码 403；
2. 以超级管理员用户登录，可正常访问所有用户/角色/权限管理接口；
3. `GET /api/v1/users/me/permissions` 能返回当前用户拥有的全部权限码列表（已去重）；
4. 前端侧边栏菜单按当前用户权限显示/隐藏，无权限的系统管理子菜单不显示，全部无权限时父菜单亦不显示；
5. 前端用户/角色/权限页面的创建、编辑、删除、分配角色/权限按钮按权限显示/隐藏；
6. 前端路由守卫拦截无权限访问的页面，给出明确提示或重定向；
7. Mock 模式与真实后端模式下，上述权限控制逻辑均可正常工作。

---

## 五、文档变更记录

| 日期 | 版本 | 变更内容 |
|---|---|---|
| 2026-03-19 | V1 | 初版项目说明书：架构、目录、前后端模块、数据模型、开发约定、环境搭建、API 接口规范 |
| 2026-03-19 | V1 补 | 前端对接真实后端（认证 + 系统管理，用户/角色/权限 CRUD） |
| 2026-03-20 | V1 补 | 业务模块页面全面对接新 API 类型；知识库完整功能（MinIO + 分段预览） |
| 2026-10-25 | V2 | 新增 RBAC 授权功能：后端接口权限拦截依赖、`GET /users/me/permissions` 接口、接口权限拦截清单；前端菜单/按钮/路由守卫权限控制；权限码设计规范与验收标准 |

---

> 本文档为需求分析产出，**不包含任何实现代码**。后续开发阶段应按本文档的接口清单、权限码规范与验收标准进行后端 Service/Controller 编写及前端页面改造。