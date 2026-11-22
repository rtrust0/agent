# 辰光 Agent 平台 — 项目说明书 V3（RBAC 授权需求增量 · 全业务模块）

> 文档定位：在 `docs/PROJECT_SPEC.md`（V1）基础上，基于 `docs/spec/PROJECT_SPEC_V2.md` 编写，定义 **RBAC 授权功能** 的需求增量，覆盖全部业务模块。
> 未在本文中提及的模块、页面、接口、数据表，均保持 V1 现状不变。

---

## 一、增量范围

### 1.1 基线

| 文档 | 内容 | 本文关系 |
|---|---|---|
| `docs/PROJECT_SPEC.md`（V1） | 项目全貌：架构、目录、模块、数据模型、开发规范、环境搭建 | **基线**：未提及部分一律沿用 V1 |
| `docs/spec/PROJECT_SPEC_V2.md`（V2） | RBAC 授权（用户 / 角色 / 权限 / 系统管理的接口拦截与前端控制） | **前置增量**：本文在其基础上扩展 |
| 本文（V3） | RBAC 授权在**全部业务模块**的需求增量 + 数据权限 / 审计 / 审批 | **增量**：只定义变化 |

### 1.2 本文新增（相对 V2）

1. **授权覆盖范围**：从 user / role / permission / system 四个模块，扩展到 V1 的全部业务模块——工作台、Agent 管理、模型管理、Prompt 管理、知识库管理、工具管理、对话日志、数据统计、系统管理。
2. **全模块权限码体系**：为每个业务模块定义 `模块:操作` 权限码，共 **71 个**（核心 27 + 业务 44）。
3. **资源级数据权限**：`users.data_scope` 字段 + 查询过滤规则（本人 / 部门 / 全量）。
4. **权限操作审计日志**：`audit_logs` 表 + 写操作自动记录。
5. **权限申请与审批流程**：`permission_applications` 表 + 申请 / 审批接口。
6. **前端全模块控制**：所有业务模块的菜单、按钮、路由守卫按权限码显隐。

### 1.3 本文不改

- V1 中未提及的模块、页面、接口、数据表，**保持 V1 现状不变**。
- V2 已完成的核心授权机制（`get_current_user_with_permission`、`/users/me/permissions`）**复用，不重写**。
- 业务模块自身的功能行为（CRUD 语义、字段、响应结构）不变，本文只在其上**增加授权判定**。

---

## 二、权限码体系（全模块）

### 2.1 规范

- 格式：`模块:操作`，全部小写，操作名用下划线分隔（如 `agent:publish`、`knowledge:document_upload`）。
- 超级管理员 `User.is_superuser == true` 拥有全部权限：权限校验时直接放行。
- 权限不足：`BizException(code=403, message="没有权限执行该操作")`，全局异常处理器返回 HTTP 200 + 业务码 403（沿用 V2 约定）。

### 2.2 核心 RBAC 权限码（27 个）

#### 2.2.1 V2 已有（22 个）

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

#### 2.2.2 V3 新增（5 个）

| 模块 | 权限码 | 含义 |
|---|---|---|
| data_scope | `data_scope:own` | 本人数据权限（仅本人创建/负责的数据） |
| data_scope | `data_scope:dept` | 部门数据权限（本部门数据） |
| data_scope | `data_scope:all` | 全量数据权限（无数据隔离） |
| approval | `approval:apply` | 发起权限申请 |
| approval | `approval:audit` | 审批权限申请 |

### 2.3 业务模块权限码（44 个）

#### 2.3.1 工作台（dashboard）

| 权限码 | 含义 |
|---|---|
| `dashboard:read` | 查看工作台统计、趋势、排行榜、告警、资源用量 |

#### 2.3.2 Agent 管理（agent）

| 权限码 | 含义 |
|---|---|
| `agent:list` | Agent 列表查看 |
| `agent:read` | Agent 详情查看 |
| `agent:create` | 创建 Agent |
| `agent:update` | 更新 Agent |
| `agent:delete` | 删除 Agent |
| `agent:publish` | 发布 / 下线 Agent |
| `agent:test` | Agent 调试测试 |
| `agent:monitor` | Agent 监控查看 |

#### 2.3.3 模型管理（model）

| 权限码 | 含义 |
|---|---|
| `model:list` | 模型列表查看 |
| `model:read` | 模型详情查看 |
| `model:create` | 创建模型 |
| `model:update` | 更新模型 |
| `model:delete` | 删除模型 |
| `model:provider_manage` | 模型供应商管理 |
| `model:test` | 模型 / 供应商连接测试 |

#### 2.3.4 Prompt 管理（prompt）

| 权限码 | 含义 |
|---|---|
| `prompt:list` | Prompt 列表查看 |
| `prompt:read` | Prompt 详情查看 |
| `prompt:create` | 创建 Prompt |
| `prompt:update` | 更新 Prompt |
| `prompt:delete` | 删除 Prompt |
| `prompt:publish` | 发布 / 回滚 Prompt 版本 |
| `prompt:test` | Prompt 调试测试 |

#### 2.3.5 知识库管理（knowledge）

| 权限码 | 含义 |
|---|---|
| `knowledge:list` | 知识库列表查看 |
| `knowledge:read` | 知识库详情 / 文档 / 分段查看 |
| `knowledge:create` | 创建知识库 |
| `knowledge:update` | 更新知识库配置 |
| `knowledge:delete` | 删除知识库 |
| `knowledge:document_upload` | 上传 / 重试文档 |
| `knowledge:document_delete` | 删除文档 / 分段 |
| `knowledge:retrieval_test` | 检索测试 |
| `knowledge:reindex` | 重新索引 |

#### 2.3.6 工具管理（tool）

| 权限码 | 含义 |
|---|---|
| `tool:list` | 工具列表查看 |
| `tool:read` | 工具详情 / 调用日志查看 |
| `tool:create` | 注册工具 |
| `tool:update` | 更新工具 |
| `tool:delete` | 删除工具 |
| `tool:test` | 工具测试 |
| `tool:toggle` | 启用 / 禁用工具 |

#### 2.3.7 对话日志（conversation）

| 权限码 | 含义 |
|---|---|
| `conversation:list` | 对话列表查看 |
| `conversation:read` | 对话详情 / 轮次 / 链路追踪查看 |
| `conversation:annotate` | 对话标注 |
| `conversation:export` | 对话导出 |

#### 2.3.8 数据统计（analytics）

| 权限码 | 含义 |
|---|---|
| `analytics:read` | 查看用量、费用、效果评估等统计 |

> **说明**：V2 及既有计划中 `analytics`、`dashboard` 未定义权限码（仅登录即可访问）。V3 将其纳入授权范围，这是本文对既有计划的**显式变更**；接口仍要求登录，但还需对应权限码。

### 2.4 权限码总计

| 分组 | 数量 |
|---|---:|
| 核心 RBAC（V2 22 + V3 新增 5） | 27 |
| 业务模块（dashboard/agent/model/prompt/knowledge/tool/conversation/analytics） | 44 |
| **合计** | **71** |

---

## 三、后端增量

### 3.1 授权依赖（复用 V2，不重写）

沿用 V2 已实现的：

```python
# src/core/deps.py（V2 已完成）
def get_user_permission_codes(user: User) -> set[str]: ...
def get_current_user_with_permission(permission_code: str): ...
```

V3 仅将 `get_current_user_with_permission("<业务权限码>")` 注入到各业务模块接口。

### 3.2 当前用户权限查询（复用 V2）

`GET /api/v1/users/me/permissions` 保持不变；V3 下它返回的权限码集合包含第 2 章的全部 71 个权限码中该用户实际拥有的部分（超管返回全部已定义权限码）。

> 实现要求：超管返回的列表必须从**数据库中已定义的权限**实时推导（`SELECT code FROM permissions`），而非代码内常量，确保新增业务权限码后自动纳入。

### 3.3 全业务模块接口权限拦截清单

#### 3.3.1 工作台（已有计划：`dashboard-plan.md`）

| 接口 | 方法 | 所需权限码 |
|---|---|---|
| `/api/v1/dashboard/stats` | GET | `dashboard:read` |
| `/api/v1/dashboard/trends` | GET | `dashboard:read` |
| `/api/v1/dashboard/top-agents` | GET | `dashboard:read` |
| `/api/v1/dashboard/recent-alerts` | GET | `dashboard:read` |
| `/api/v1/dashboard/resource-usage` | GET | `dashboard:read` |

#### 3.3.2 对话日志（已有计划：`conversation-plan.md`）

| 接口 | 方法 | 所需权限码 |
|---|---|---|
| `/api/v1/conversations` | GET | `conversation:list` |
| `/api/v1/conversations/{id}` | GET | `conversation:read` |
| `/api/v1/conversations/{id}/turns` | GET | `conversation:read` |
| `/api/v1/turns/{turn_id}/trace` | GET | `conversation:read` |
| `/api/v1/conversations/{id}/annotate` | POST | `conversation:annotate` |
| `/api/v1/conversations/{id}/export` | GET | `conversation:export` |

#### 3.3.3 数据统计（已有计划：`analytics-plan.md`）

| 接口 | 方法 | 所需权限码 |
|---|---|---|
| `/api/v1/analytics/overview` | GET | `analytics:read` |
| `/api/v1/analytics/daily` | GET | `analytics:read` |
| `/api/v1/analytics/by-agent` | GET | `analytics:read` |
| `/api/v1/analytics/by-model` | GET | `analytics:read` |
| `/api/v1/analytics/costs` | GET | `analytics:read` |
| `/api/v1/analytics/evaluation` | GET | `analytics:read` |

#### 3.3.4 系统管理扩展（已有计划：`system-extension-plan.md`）

| 接口 | 方法 | 所需权限码 |
|---|---|---|
| `/api/v1/system/api-keys` | GET / POST / PUT / DELETE | `system:api_keys` |
| `/api/v1/system/audit-logs` | GET | `system:audit` |
| `/api/v1/system/audit-logs/export` | GET | `system:audit` |
| `/api/v1/system/alerts/rules` | GET / POST / PUT / DELETE | `system:alerts` |
| `/api/v1/system/alerts/active` | GET | `system:alerts` |
| `/api/v1/system/alerts/{id}/acknowledge` | POST | `system:alerts` |
| `/api/v1/system/alerts/{id}/resolve` | POST | `system:alerts` |
| `/api/v1/system/settings` | GET / PUT | `system:settings` |

#### 3.3.5 Agent / 模型 / Prompt / 知识库 / 工具（后端待实现，本文定义规格）

> 以下模块后端尚未实现（V1 §九）。本文先定义**权限码与拦截规则**，后端实现时按此注入。

| 模块 | 接口（按 V1 模块能力与 RESTful 约定） | 方法 | 所需权限码 |
|---|---|---|---|
| Agent | `/api/v1/agents` | GET | `agent:list` |
| Agent | `/api/v1/agents/{id}` | GET | `agent:read` |
| Agent | `/api/v1/agents` | POST | `agent:create` |
| Agent | `/api/v1/agents/{id}` | PUT | `agent:update` |
| Agent | `/api/v1/agents/{id}` | DELETE | `agent:delete` |
| Agent | `/api/v1/agents/{id}/publish` | POST | `agent:publish` |
| Agent | `/api/v1/agents/{id}/test` | POST | `agent:test` |
| Agent | `/api/v1/agents/{id}/monitor` | GET | `agent:monitor` |
| Agent | `/api/v1/agents/{id}/versions` | GET | `agent:read` |
| Agent | `/api/v1/agents/{id}/versions/{version}/rollback` | POST | `agent:publish` |
| 模型 | `/api/v1/models` | GET | `model:list` |
| 模型 | `/api/v1/models/{id}` | GET | `model:read` |
| 模型 | `/api/v1/models` | POST | `model:create` |
| 模型 | `/api/v1/models/{id}` | PUT | `model:update` |
| 模型 | `/api/v1/models/{id}` | DELETE | `model:delete` |
| 模型 | `/api/v1/models/providers` | GET / POST / PUT / DELETE | `model:provider_manage` |
| 模型 | `/api/v1/models/{id}/test` | POST | `model:test` |
| Prompt | `/api/v1/prompts` | GET | `prompt:list` |
| Prompt | `/api/v1/prompts/{id}` | GET | `prompt:read` |
| Prompt | `/api/v1/prompts` | POST | `prompt:create` |
| Prompt | `/api/v1/prompts/{id}` | PUT | `prompt:update` |
| Prompt | `/api/v1/prompts/{id}` | DELETE | `prompt:delete` |
| Prompt | `/api/v1/prompts/{id}/publish` | POST | `prompt:publish` |
| Prompt | `/api/v1/prompts/{id}/versions/{version}/rollback` | POST | `prompt:publish` |
| Prompt | `/api/v1/prompts/{id}/test` | POST | `prompt:test` |
| 知识库 | `/api/v1/knowledge-bases` | GET | `knowledge:list` |
| 知识库 | `/api/v1/knowledge-bases/{id}` | GET | `knowledge:read` |
| 知识库 | `/api/v1/knowledge-bases` | POST | `knowledge:create` |
| 知识库 | `/api/v1/knowledge-bases/{id}` | PUT | `knowledge:update` |
| 知识库 | `/api/v1/knowledge-bases/{id}` | DELETE | `knowledge:delete` |
| 知识库 | `/api/v1/knowledge-bases/{id}/documents` | POST | `knowledge:document_upload` |
| 知识库 | `/api/v1/knowledge-bases/{id}/documents/{doc_id}/retry` | POST | `knowledge:document_upload` |
| 知识库 | `/api/v1/knowledge-bases/{id}/documents/{doc_id}` | DELETE | `knowledge:document_delete` |
| 知识库 | `/api/v1/knowledge-bases/{id}/segments` | GET | `knowledge:read` |
| 知识库 | `/api/v1/knowledge-bases/{id}/retrieval-test` | POST | `knowledge:retrieval_test` |
| 知识库 | `/api/v1/knowledge-bases/{id}/reindex` | POST | `knowledge:reindex` |
| 工具 | `/api/v1/tools` | GET | `tool:list` |
| 工具 | `/api/v1/tools/{id}` | GET | `tool:read` |
| 工具 | `/api/v1/tools` | POST | `tool:create` |
| 工具 | `/api/v1/tools/{id}` | PUT | `tool:update` |
| 工具 | `/api/v1/tools/{id}` | DELETE | `tool:delete` |
| 工具 | `/api/v1/tools/{id}/test` | POST | `tool:test` |
| 工具 | `/api/v1/tools/{id}/toggle` | POST | `tool:toggle` |
| 工具 | `/api/v1/tools/{id}/logs` | GET | `tool:read` |

#### 3.3.6 保持开放的接口（不变）

以下接口在 V3 中仍**只需登录、无需权限码**（沿用 V2 约定）：

- `GET /api/v1/users/me`
- `GET /api/v1/users/me/permissions`
- `GET /api/v1/users`、`GET /api/v1/roles/`、`GET /api/v1/permissions/`（前端分配角色 / 权限弹窗依赖）

### 3.4 资源级数据权限（V3 新增）

#### 3.4.1 模型

`users` 表新增字段 `data_scope`（`own` / `dept` / `all`，默认 `own`）。

| 值 | 含义 | 查询过滤 |
|---|---|---|
| `own` | 本人数据 | `WHERE created_by = current_user.id` |
| `dept` | 本部门数据 | `WHERE department_id = current_user.department_id` |
| `all` | 全量数据 | 无额外条件 |

#### 3.4.2 适用范围

数据权限作用于**全部业务模块的列表 / 详情查询**（dashboard、agent、model、prompt、knowledge、tool、conversation、analytics、user、role、permission、system 审计等），以及更新 / 删除操作的目标校验。

#### 3.4.3 规则

- 列表查询：按 `data_scope` 自动追加过滤条件；
- 详情 / 更新 / 删除：目标数据不在当前用户范围内时返回 403；
- 超管不受限制（等价 `all`）；
- 实现位置：Service 层（不在 Controller 中拼 SQL），沿用 V1 三层架构。

### 3.5 权限操作审计日志（V3 新增）

#### 3.5.1 表 `audit_logs`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| user_id | INTEGER | 操作用户 ID |
| username | VARCHAR(100) | 操作用户名（冗余） |
| action | VARCHAR(50) | create / update / delete / assign / approve / apply / export |
| module | VARCHAR(50) | user / role / permission / agent / model / prompt / knowledge / tool / conversation / analytics / system / approval |
| target_id | VARCHAR(100) | 被操作资源 ID |
| target_name | VARCHAR(200) | 被操作资源名称 |
| detail | TEXT | 变更前后对比（JSON） |
| ip_address | VARCHAR(50) | 操作者 IP |
| created_at | DATETIME | 操作时间 |

#### 3.5.2 记录范围

**全部业务模块的写操作**（create / update / delete / assign / publish / rollback / upload / toggle / annotate / approve / apply / export）自动记录；读操作不记录。记录方式：Service 层统一审计切面 / 装饰器。

#### 3.5.3 接口

| 接口 | 方法 | 所需权限码 |
|---|---|---|
| `/api/v1/system/audit-logs` | GET | `system:audit` |
| `/api/v1/system/audit-logs/export` | GET | `system:audit` |

### 3.6 权限申请与审批流程（V3 新增）

#### 3.6.1 表 `permission_applications`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| applicant_id | INTEGER | 申请人 ID |
| applicant_name | VARCHAR(100) | 申请人姓名（冗余） |
| permission_code | VARCHAR(100) | 申请的权限码（71 个之一） |
| reason | TEXT | 申请理由 |
| status | VARCHAR(20) | pending / approved / rejected / expired |
| approver_id | INTEGER | 审批人 ID |
| approver_name | VARCHAR(100) | 审批人姓名 |
| approved_at | DATETIME | 审批时间 |
| expired_at | DATETIME | 过期时间（空 = 永久） |
| created_at | DATETIME | 申请时间 |

#### 3.6.2 接口

| 接口 | 方法 | 所需权限码 |
|---|---|---|
| `/api/v1/approvals/apply` | POST | `approval:apply` |
| `/api/v1/approvals/my` | GET | `approval:apply` |
| `/api/v1/approvals/list` | GET | `approval:audit` |
| `/api/v1/approvals/{id}/audit` | PUT | `approval:audit` |

#### 3.6.3 审批生效

- 通过且 `expired_at` 为空：永久授予该权限码；
- 通过且 `expired_at` 不为空：临时授予，到期自动回收；
- 拒绝：状态置 `rejected`，不授予。

### 3.7 数据表增量汇总

| 对象 | 变更 | 说明 |
|---|---|---|
| `users` | 新增字段 `data_scope`、`created_by` | 数据权限范围与数据归属 |
| `audit_logs` | 新增表 | 权限操作审计日志 |
| `permission_applications` | 新增表 | 权限申请与审批 |

> 除上表外，V1 已有数据表结构保持不变。

### 3.8 数据库脚本对照

本文的增量已落地为：

| 文件 | 内容 |
|---|---|
| `docs/design/db/script.sql` | 7 张表（users / roles / permissions / user_roles / role_permissions / audit_logs / permission_applications）+ 索引 |
| `docs/design/db/init-data.sql` | 27 个核心权限码 + 3 角色 + 3 演示账号 + 授权关系 |
| `docs/design/db/rbac.db` | SQLite 开发库 |

> 业务模块的 44 个权限码需在本文定稿后追加到 `init-data.sql` 与初始化数据中（当前脚本仅含 27 个核心权限码）。

---

## 四、前端增量

### 4.1 权限获取（复用 V2）

`getCurrentUserPermissions()` 调用 `GET /api/v1/users/me/permissions`，权限码集合存入全局状态；`hasPerm(code)` 供菜单 / 按钮 / 路由消费。V3 下集合包含业务模块权限码。

### 4.2 菜单权限过滤（全模块）

| 菜单项 | 路由 | 所需权限码 |
|---|---|---|
| 工作台 | `/` | `dashboard:read` |
| Agent 管理 | `/agents` | `agent:list` |
| 模型管理 | `/models` | `model:list` |
| 模型供应商 | `/models/providers` | `model:provider_manage` |
| Prompt 管理 | `/prompts` | `prompt:list` |
| 知识库管理 | `/knowledge` | `knowledge:list` |
| 工具管理 | `/tools` | `tool:list` |
| 对话日志 | `/conversations` | `conversation:list` |
| 数据统计 | `/analytics` | `analytics:read` |
| 用户管理 | `/system/users` | `user:list` |
| 角色管理 | `/system/roles` | `role:list` |
| 权限管理 | `/system/permissions` | `permission:list` |
| API 密钥 | `/system/api-keys` | `system:api_keys` |
| 审计日志 | `/system/audit` | `system:audit` |
| 告警规则 | `/system/alerts` | `system:alerts` |
| 系统配置 | `/system/settings` | `system:settings` |
| 权限申请 | `/system/approvals` | `approval:apply` 或 `approval:audit` |

控制逻辑沿用 V2：无权限不渲染；父菜单下全部子项无权限时父菜单隐藏。

### 4.3 按钮权限过滤（全模块）

| 页面 | 按钮 / 操作 | 所需权限码 |
|---|---|---|
| 工作台 | 查看统计（页面级） | `dashboard:read` |
| Agent 列表 | 创建 / 编辑 / 删除 / 发布 / 测试 / 监控 | `agent:create` / `agent:update` / `agent:delete` / `agent:publish` / `agent:test` / `agent:monitor` |
| 模型列表 | 创建 / 编辑 / 删除 / 测试；供应商管理 | `model:create` / `model:update` / `model:delete` / `model:test`；`model:provider_manage` |
| Prompt 列表 | 创建 / 编辑 / 删除 / 发布 / 回滚 / 测试 | `prompt:create` / `prompt:update` / `prompt:delete` / `prompt:publish` / `prompt:test` |
| 知识库详情 | 上传 / 重试文档 / 删除文档 / 检索测试 / 重新索引 / 删除知识库 | `knowledge:document_upload` / `knowledge:document_delete` / `knowledge:retrieval_test` / `knowledge:reindex` / `knowledge:delete` |
| 工具列表 | 注册 / 编辑 / 删除 / 测试 / 启停 | `tool:create` / `tool:update` / `tool:delete` / `tool:test` / `tool:toggle` |
| 对话详情 | 标注 / 导出 | `conversation:annotate` / `conversation:export` |
| 用户管理 | 添加 / 删除 / 分配角色 | `user:create` / `user:delete` / `user:assign_roles` |
| 角色管理 | 创建 / 编辑 / 删除 / 分配权限 | `role:create` / `role:update` / `role:delete` / `role:assign_permissions` |
| 权限管理 | 创建 / 编辑 / 删除 | `permission:create` / `permission:update` / `permission:delete` |
| 审计日志 | 导出 | `system:audit` |
| 告警规则 | 创建 / 编辑 / 删除 / 确认 / 解决 | `system:alerts` |
| 系统配置 | 保存 | `system:settings` |
| 权限申请 | 发起 / 审批 | `approval:apply` / `approval:audit` |

### 4.4 路由守卫（全模块）

`AuthGuard` 接受 `requiredPermission`（沿用 V2 扩展），所有业务模块路由按 4.2 的权限码包裹：

- `/agents/*` → `agent:list`
- `/models/*` → `model:list`（`/models/providers` → `model:provider_manage`）
- `/prompts/*` → `prompt:list`
- `/knowledge/*` → `knowledge:list`
- `/tools/*` → `tool:list`
- `/conversations/*` → `conversation:list`
- `/analytics/*` → `analytics:read`
- `/` → `dashboard:read`
- `/system/*` → 对应权限码（同 4.2）

无权限时：重定向到 `/login` 或展示「无权访问该页面」提示页（沿用 V2 选型），建议优先展示 403 页。

### 4.5 数据权限 UI

各业务模块列表页展示当前数据范围标识（本人 / 本部门 / 全量）；数据过滤由后端完成，前端不重复过滤。

### 4.6 审计日志页面

`/system/audit` 展示审计日志（时间、操作人、动作、模块、目标、详情、IP），支持分页与过滤，需要 `system:audit`。

### 4.7 权限申请页面

- `/system/approvals/apply`：发起申请（`approval:apply`）
- `/system/approvals/my`：我的申请（`approval:apply`）
- `/system/approvals/list`：审批列表（`approval:audit`）

---

## 五、验收标准（增量）

### 5.1 V2 验收标准（已完成，保持不变）

1. 非超管调用需权限接口返回业务码 403；
2. 超管可访问全部用户 / 角色 / 权限接口；
3. `/users/me/permissions` 返回去重权限码列表；
4. 侧边栏菜单按权限显隐；
5. 用户 / 角色 / 权限页按钮按权限显隐；
6. 路由守卫拦截无权页面；
7. Mock 与真实后端下权限控制均生效。

### 5.2 V3 新增验收标准

8. **全模块菜单**：无对应权限码时，工作台、Agent、模型、Prompt、知识库、工具、对话、统计菜单均不渲染；
9. **全模块按钮**：各业务模块页面的创建 / 编辑 / 删除 / 发布 / 测试等按钮按权限码显隐；
10. **全模块路由**：直接访问无权限的业务模块路由时被拦截（403 或重定向）；
11. **数据权限**：`own` 仅见本人数据、`dept` 仅见本部门数据、`all` 见全量数据；越权访问详情 / 修改返回 403；
12. **审计日志**：全部业务模块写操作自动生成审计记录，可在 `/system/audit` 按模块 / 动作 / 操作人查询；
13. **权限申请**：用户发起申请 → 审批人通过 → 权限立即生效；拒绝不生效；临时授权到期回收；
14. **权限码完整性**：数据库 `permissions` 表包含第 2 章全部 71 个权限码，且 `/users/me/permissions` 对超管返回全部 71 个。

---

## 六、变更记录

| 日期 | 版本 | 变更内容 |
|---|---|---|
| 2026-03-19 | V1 | 初版项目说明书：架构、目录、前后端模块、数据模型、开发约定、环境搭建、API 接口规范 |
| 2026-03-19 | V1 补 | 前端对接真实后端（认证 + 系统管理，用户/角色/权限 CRUD） |
| 2026-03-20 | V1 补 | 业务模块页面全面对接新 API 类型；知识库完整功能（MinIO + 分段预览） |
| 2026-10-25 | V2 | 新增 RBAC 授权功能：后端接口权限拦截依赖、`GET /users/me/permissions` 接口、接口权限拦截清单；前端菜单/按钮/路由守卫权限控制；权限码设计规范与验收标准 |
| 2026-11-08 | V3 | 重新定位为「基于 V1、在 V2 之上的 RBAC 授权需求增量，覆盖全部业务模块」；扩展权限码至 71 个（核心 27 + 业务 44）；新增全模块接口拦截清单、菜单/按钮/路由控制；新增资源级数据权限（`users.data_scope`）、权限操作审计日志（`audit_logs`）、权限申请与审批（`permission_applications`）；新增 V3 验收标准（第 8~14 条）；明确未提及项保持 V1 现状 |

---

> 本文档为需求增量说明，**不包含实现代码**。V1 未提及的模块、页面、接口、数据表保持现状；本文提及的增量按接口清单、权限码规范与验收标准实施。
