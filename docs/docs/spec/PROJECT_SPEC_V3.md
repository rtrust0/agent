# 辰光 Agent 平台 — 项目说明书 V3（RBAC 授权功能完成版与资源级数据权限规划）

> 本版本基于 `docs/PROJECT_SPEC.md`（V1）的全部内容，在 `docs/spec/PROJECT_SPEC_V2.md`（V2，RBAC 授权功能增强版）的基础上，标记 RBAC 授权功能为已完成，并新增 **资源级数据权限、权限操作审计日志、权限申请与审批流程、前端单元测试** 等 V3 新增功能。V3 作为全新 PRD，可直接供后续开发参考。

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
| 后端 — RBAC 模块（用户/角色/权限/认证/验证码） | ✅ 已实现 |
| 后端 — RBAC 授权（接口权限拦截、当前用户权限查询） | ✅ **V2 已完成** |
| 后端 — 资源级数据权限（本人/部门/全量数据隔离） | ❌ **V3 新增，待实现** |
| 后端 — 权限操作审计日志 | ❌ **V3 新增，待实现** |
| 后端 — 权限申请与审批流程 | ❌ **V3 新增，待实现** |
| 后端 — Agent/模型/Prompt/知识库/工具等业务模块 | ❌ 待实现 |
| 前端 — 全部页面 UI + Mock 数据 | ✅ 已实现 |
| 前端 — 对接真实后端 API（用户/角色/权限 CRUD） | ✅ 已完成 |
| 前端 — 菜单/按钮/路由基于权限的显示控制 | ✅ **V2 已完成** |
| 前端 — 资源级数据权限 UI 控制 | ❌ **V3 新增，待实现** |
| 前端 — 前端单元测试（Vitest/Jest） | ❌ **V3 新增，待实现** |

---

## 二、RBAC 授权功能（V2 已完成）

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

以上目标在 V2 阶段已全部实现并通过验收。

### 2.3 非目标（V2 阶段不做，已在 V3 中重新纳入规划）

V2 阶段明确不做以下功能，已在 V3 中作为新增需求提出：
- 资源级数据权限（本人/部门/全量数据隔离）→ 见第 3.1 节
- 权限操作审计日志 → 见第 3.2 节
- 权限申请与审批流程 → 见第 3.3 节
- 前端单元测试（Vitest/Jest 尚未引入）→ 见第 3.4 节

### 2.4 权限码设计规范

权限码格式：**`模块:操作`**，全部小写。

#### 2.4.1 V2 已有权限码（22 个）

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

#### 2.4.2 V3 新增权限码

| 模块 | 权限码 | 含义 |
|---|---|---|
| data_scope | `data_scope:own` | 本人数据权限（仅本人创建/负责的数据） |
| data_scope | `data_scope:dept` | 部门数据权限（本部门数据） |
| data_scope | `data_scope:all` | 全量数据权限（无数据隔离） |
| approval | `approval:apply` | 发起权限申请 |
| approval | `approval:audit` | 审批权限申请 |

---

## 三、后端需求（V2 已完成 + V3 新增）

### 3.1 V2 后端需求（已完成）

#### 3.1.1 新增依赖注入：带权限码的当前用户获取

在 `src/core/deps.py` 中新增依赖函数 `get_current_user_with_permission(permission_code: str)`：

1. 复用现有 `get_current_user()` 完成 JWT 校验并获取当前用户 `User` 对象（含 `roles`，`lazy="selectin"` 立即加载）；
2. 若用户 `is_superuser == true`，直接返回用户，无需校验权限码；
3. 否则遍历用户的所有角色及其关联权限，提取权限码集合；
4. 若请求的 `permission_code` 在用户权限码集合中，返回用户；
5. 若不在，抛出 `BizException(code=403, message="没有权限执行该操作")`，全局异常处理器将其返回为 HTTP 200 + 业务错误码 403。

#### 3.1.2 新增接口：当前用户权限查询

| 项目 | 内容 |
|---|---|
| 路由 | `GET /api/v1/users/me/permissions` |
| 摘要 | 获取当前登录用户拥有的所有权限码 |
| 依赖 | `get_current_user`（仅需登录，无需特定权限码）|
| 返回 | `ResponseSchema[list[str]]`，权限码字符串列表（已去重）|
| 超管行为 | 返回系统中全部已定义权限码 |

#### 3.1.3 接口权限拦截清单

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

#### 3.1.4 错误响应约定

- 权限不足：HTTP 200，`{"code": 403, "message": "没有权限执行该操作", "data": null}`（遵循现有 `BizException` 约定）；
- 未登录 / token 过期：HTTP 401，前端 `ApiClient` 已处理自动跳转 `/login`。

#### 3.1.5 数据库模型变更

- **无需新增数据库表**，复用现有 `users`、`roles`、`permissions`、`user_roles`、`role_permissions`；
- ORM 模型不变，无需新增 Alembic 迁移；
- 建议：初始化种子数据，预置 `admin` 超级管理员角色及常用权限码，供首次部署后直接使用。

---

### 3.2 V3 新增：资源级数据权限（本人/部门/全量数据隔离）

#### 3.2.1 需求背景

V2 的 RBAC 授权仅做“能否访问接口”的粒度控制（菜单/按钮/路由显隐、接口 403 拦截），无法区分“能看到哪些数据”。例如：
- 运营人员只能编辑自己创建的用户，不能编辑其他人创建的用户；
- 部门主管能看到本部门所有人的数据，不能看到其他部门数据；
- 超级管理员能看到全量数据。

V3 引入**数据权限范围（Data Scope）**概念，在查询类接口中根据当前用户的数据权限自动追加 WHERE 条件，实现行级数据隔离。

#### 3.2.2 数据权限模型

在 `User` 模型中新增字段 `data_scope`（字符串，取值 `own` / `dept` / `all`），默认 `own`：

| 值 | 含义 | SQL 过滤示例 |
|---|---|---|
| `own` | 本人数据权限 | `WHERE created_by = current_user_id` |
| `dept` | 部门数据权限 | `WHERE department_id = current_user.department_id` |
| `all` | 全量数据权限 | 无额外 WHERE 条件（超管或拥有该权限的角色） |

#### 3.2.3 接口层

在查询类接口（如 `GET /api/v1/users/search`、`GET /api/v1/roles/search`、`GET /api/v1/permissions/search`、`GET /api/v1/users` 等列表接口）中，根据当前用户的 `data_scope` 自动追加数据隔离条件。

新增依赖（可选）：`get_current_user_with_data_scope()`，在 Service 层根据 `current_user.data_scope` 注入查询过滤条件。

- `own`：`query.filter(model.created_by == current_user.id)`
- `dept`：`query.filter(model.department_id == current_user.department_id)`
- `all`：无过滤

创建/更新/删除操作时，同样校验目标数据是否在当前用户的数据权限范围内，越权返回 403。

---

### 3.3 V3 新增：权限操作审计日志

#### 3.3.1 需求背景

记录谁在什么时间、从什么 IP、对哪个资源执行了什么操作，变更前后是什么内容，用于安全审计、合规检查和问题追溯。

#### 3.3.2 审计日志模型

新增表 `audit_logs`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BigInteger | 主键，自增 |
| user_id | BigInteger | 操作用户 ID |
| username | String(100) | 操作用户名（冗余，方便查询） |
| action | String(50) | 操作类型（create / update / delete / assign / approve / apply 等） |
| module | String(50) | 操作模块（user / role / permission / approval / system 等） |
| target_id | String(100) | 被操作资源 ID |
| target_name | String(200) | 被操作资源名称 |
| detail | Text | 操作详情（变更前后对比，JSON 格式） |
| ip_address | String(50) | 操作者 IP 地址 |
| created_at | DateTime | 操作时间 |

#### 3.3.3 实现方式

在 API 层或 Service 层通过装饰器/拦截器自动记录写操作（create / update / delete / assign_roles / assign_permissions / approval apply / approval audit）的审计日志，写入 `audit_logs` 表。读操作不记录。

新增接口：
| 接口 | 方法 | 所需权限码 | 说明 |
|---|---|---|---|
| `/api/v1/audit-logs` | GET | `system:audit` | 查询审计日志列表（分页、按用户/模块/动作过滤） |

---

### 3.4 V3 新增：权限申请与审批流程

#### 3.4.1 需求背景

用户没有某个权限时，不应由管理员后台手动授权，而应支持用户自助发起申请，由指定审批人审批后临时或永久授予该权限，全程可追溯。

#### 3.4.2 权限申请模型

新增表 `permission_applications`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BigInteger | 主键，自增 |
| applicant_id | BigInteger | 申请人 ID |
| applicant_name | String(100) | 申请人姓名（冗余） |
| permission_code | String(100) | 申请的权限码 |
| reason | Text | 申请理由 |
| status | String(20) | 状态（pending / approved / rejected / expired） |
| approver_id | BigInteger | 审批人 ID（可为空） |
| approver_name | String(100) | 审批人姓名（可为空） |
| approved_at | DateTime | 审批时间（可为空） |
| expired_at | DateTime | 权限过期时间（临时授权时填写，可为空表示永久） |
| created_at | DateTime | 申请时间 |

#### 3.4.3 接口

| 接口 | 方法 | 所需权限码 | 说明 |
|---|---|---|---|
| `/api/v1/approvals/apply` | POST | `approval:apply` | 发起权限申请，body: `{permission_code, reason}` |
| `/api/v1/approvals/list` | GET | `approval:audit` | 查询申请列表（分页，按状态过滤） |
| `/api/v1/approvals/{id}/audit` | PUT | `approval:audit` | 审批申请，body: `{status: approved|rejected, remark?}` |
| `/api/v1/approvals/my` | GET | `approval:apply` | 查询我的申请列表 |

审批通过后：
- 若 `expired_at` 为空，永久将权限码加入用户角色或直接赋予用户；
- 若 `expired_at` 不为空，临时授权，到期后自动回收。

前端对应新增“权限申请”页面，在侧边栏“系统管理”下显示（需要 `approval:apply` 或 `approval:audit`）。

---

## 四、前端需求（V2 已完成 + V3 新增）

### 4.1 V2 前端需求（已完成）

前端通过 `VITE_USE_MOCK` 开关在 Mock 与真实 API 之间切换，授权控制需在两种模式下都能工作。Mock 模式下可模拟返回当前用户权限码列表。

#### 4.1.1 当前用户权限获取

- 在 `app/src/services/system.ts`（或 `app/src/services/auth.ts`）中新增 `getCurrentUserPermissions()`：
  - 真实后端：调用 `GET /api/v1/users/me/permissions`，返回 `string[]`；
  - Mock 模式：从 mock 数据中返回预设的权限码列表；
- 登录成功后及页面初始化时调用一次，将权限码集合存储在全局状态（React Context）或页面局部状态，供菜单、按钮、路由守卫消费。

#### 4.1.2 侧边栏菜单权限过滤（`app/src/layouts/DashboardLayout.tsx`）

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
| 权限申请 | `/system/approvals` | `approval:apply` / `approval:audit` |

控制逻辑：
- 当前用户不具备菜单项所需权限时，该菜单项不渲染；
- 若“系统管理”下所有子菜单均因无权限被隐藏，则“系统管理”父菜单也不显示；
- 当前用户无任何可见菜单时，侧边栏仅保留 Logo 与用户区域。

#### 4.1.3 操作按钮权限过滤（各 system 页面）

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

#### 4.1.4 路由守卫扩展（`app/src/components/AuthGuard.tsx`）

现有 `AuthGuard` 仅校验 `authService.isLoggedIn()`，未登录跳转 `/login`。

新增扩展：
- `AuthGuard` 接受可选的 `requiredPermission?: string` 属性；
- 若指定 `requiredPermission`，则校验当前用户权限集合是否包含该权限码；
- 无权限时：重定向到 `/login` 或展示“无权访问该页面”提示页（两种方式供选型，建议优先重定向并携带错误提示）；
- 所有 `/system/*` 路由可按需包裹带权限码的 `AuthGuard`，实现页面级访问控制。

#### 4.1.5 前后端接口契约

| 场景 | 后端返回 | 前端处理 |
|---|---|---|
| 权限足够 | HTTP 200 + 正常业务数据 | 正常渲染页面/执行操作 |
| 权限不足 | HTTP 200 + `{"code": 403, "message": "没有权限执行该操作", "data": null}` | 捕获业务错误码 403，提示用户“无权执行该操作” |
| 未登录/Token 过期 | HTTP 401 | `ApiClient` 自动清除 token 并跳转 `/login`（已实现）|

### 4.2 V3 新增前端需求

#### 4.2.1 资源级数据权限 UI 控制

- 在列表页面（用户 / 角色 / 权限）中，根据当前用户的 `data_scope` 字段，在前端展示相应的数据过滤提示（如“仅显示本人数据”、“仅显示本部门数据”、“显示全量数据”）；
- 后端已按 `data_scope` 过滤数据，前端仅负责展示状态标识，无需额外接口。

#### 4.2.2 权限申请与审批页面

新增页面：
- `/system/approvals/apply`：权限申请页面（需要 `approval:apply`），表单包含权限码选择、申请理由；
- `/system/approvals/list`：申请列表页面（需要 `approval:audit`），显示所有申请，支持审批（通过/拒绝）；
- `/system/approvals/my`：我的申请页面（需要 `approval:apply`），显示当前用户发起的申请及状态。

侧边栏“系统管理”下新增“权限申请”菜单项，需 `approval:apply` 或 `approval:audit` 权限可见。

#### 4.2.3 审计日志页面

新增页面：
- `/system/audit`：审计日志页面（需要 `system:audit`），表格展示操作时间、操作人、操作类型、模块、目标资源、详情、IP 地址，支持分页和过滤。

侧边栏“系统管理”下已有“审计日志”菜单项（需要 `system:audit`）。

#### 4.2.4 前端单元测试（Vitest/Jest）

V3 引入前端单元测试，覆盖以下权限相关模块：

| 测试模块 | 测试内容 | 文件 |
|---|---|---|
| `usePermissions` Hook | `hasPerm` 判断、超管直放、权限缓存、切换身份后重拉 | `app/src/hooks/__tests__/usePermissions.test.ts` |
| `AuthGuard` 组件 | 有权限渲染子组件，无权限重定向 / 显示 403 | `app/src/components/__tests__/AuthGuard.test.tsx` |
| 菜单权限过滤 | 根据权限码显示/隐藏菜单项，全部无权限时隐藏父菜单 | `app/src/layouts/__tests__/menuFilter.test.ts` |
| 按钮权限组件 | 根据权限码显示/隐藏操作按钮 | `app/src/components/ui/__tests__/PermissionButton.test.tsx` |

测试框架：Vitest（或 Jest），Mock API 层，不依赖真实后端。

---

## 五、验收标准

### V2 验收标准（已通过）

1. 以非超级管理员用户登录，调用需要权限的管理接口，后端返回业务错误码 403；
2. 以超级管理员用户登录，可正常访问所有用户/角色/权限管理接口；
3. `GET /api/v1/users/me/permissions` 能返回当前用户拥有的全部权限码列表（已去重）；
4. 前端侧边栏菜单按当前用户权限显示/隐藏，无权限的系统管理子菜单不显示，全部无权限时父菜单亦不显示；
5. 前端用户/角色/权限页面的创建、编辑、删除、分配角色/权限按钮按权限显示/隐藏；
6. 前端路由守卫拦截无权限访问的页面，给出明确提示或重定向；
7. Mock 模式与真实后端模式下，上述权限控制逻辑均可正常工作。

### V3 新增验收标准

8. 具备 `data_scope:own` 的用户只能查询/编辑本人创建的数据，接口自动过滤其他用户数据；
9. 具备 `data_scope:dept` 的用户能查询/编辑本部门数据，不能看到其他部门数据；具备 `data_scope:all` 的用户可看到全量数据；
10. 权限操作（创建/更新/删除用户、创建/更新/删除角色、给角色分配权限、给用户分配角色、权限申请、审批操作）自动产生审计日志，可在 `/system/audit` 页面查询；
11. 用户发起权限申请后，审批人审批通过，申请人获得对应权限码，前端 UI 权限立即生效（无需刷新页面）；
12. 前端单元测试覆盖 `usePermissions`、`AuthGuard`、菜单权限过滤、按钮权限过滤，全部通过。

---

## 六、文档变更记录

| 日期 | 版本 | 变更内容 |
|---|---|---|
| 2026-03-19 | V1 | 初版项目说明书：架构、目录、前后端模块、数据模型、开发约定、环境搭建、API 接口规范 |
| 2026-03-19 | V1 补 | 前端对接真实后端（认证 + 系统管理，用户/角色/权限 CRUD） |
| 2026-03-20 | V1 补 | 业务模块页面全面对接新 API 类型；知识库完整功能（MinIO + 分段预览） |
| 2026-10-25 | V2 | 新增 RBAC 授权功能：后端接口权限拦截依赖、`GET /users/me/permissions` 接口、接口权限拦截清单；前端菜单/按钮/路由守卫权限控制；权限码设计规范与验收标准 |
| 2026-11-08 | V3 | RBAC 授权功能标记为已完成；新增资源级数据权限（`data_scope:own/dept/all`）、权限操作审计日志（`audit_logs` 表、`/api/v1/audit-logs` 接口）、权限申请与审批流程（`permission_applications` 表、`/api/v1/approvals/*` 接口）、前端单元测试（Vitest/Jest）；新增权限码 `data_scope:own/dept/all`、`approval:apply/audit`；新增 V3 验收标准（第 8~12 条） |

---

> 本文档为需求分析产出，**不包含任何实现代码**。后续开发阶段应按本文档的接口清单、权限码规范与验收标准进行后端 Service/Controller 编写及前端页面改造。V3 新增功能（资源级数据权限、审计日志、权限申请审批、前端单元测试）为 V2 已完成的 RBAC 授权功能之上的渐进式增强，可按优先级分阶段实施。
