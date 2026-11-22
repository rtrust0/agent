# backend · V3 全业务模块后端 Implementation Plan（Phase 2）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans（inline）。本计划承接 `2026-11-08-backend-rbac.md`（Phase 1：core/auth/user），完成 RBAC 剩余模块并实现 V3 §3.3 的全部业务模块。

**Goal:** 在 `backend/` 内补齐 role / permission / audit / approval，并按 V3 §3.3.5 实现 model / agent / prompt / knowledge / tool / conversation / dashboard / analytics / system 九个业务模块；每个模块全部 API 经 pytest 单元测试，并在 `docs/tests/backend/<module>-backend-test.md` 生成测试报告。

**Architecture:** 模块内分层 `api.py → service.py → repository.py → model.py → schema.py`，模块间仅通过 service 协作。所有权限拦截复用 `get_current_user_with_permission(code)`；数据权限在 service 层通过 `core/data_scope.py` 追加过滤；审计写入在 service 层通过 `AuditService.record` 完成，IP/UA 由 contextvar 中间件注入。

**Tech Stack:** Python 3.14 + FastAPI + SQLAlchemy 2.0 async + Pydantic v2；pytest + pytest-asyncio + httpx（内存 SQLite）。

**Spec:** `docs/spec/PROJECT_SPEC_V3.md`（§2 权限码、§3.3 拦截清单、§3.4 数据权限、§3.5 审计、§3.6 审批）
**DB:** `docs/design/db/script.sql`（23 张表）、`docs/design/db/README.md`（ER 与冲突收敛）、`docs/design/db/init-data.sql`（71 权限码）

## Global Constraints

- 全部后端代码在 `backend/`；模块路径 `backend/app/modules/<module>/{api,service,repository,model,schema}.py`。
- 响应统一 `{"code":200,"message":"success","data":...}`；分页 `PageResult{items,total,page,page_size}`；失败 HTTP 200 + 业务码（401/403/404/400）。
- 超管放行；业务权限码与 V3 §2 完全一致（71 个，`core/permission_catalog.py` 单一事实源）。
- 测试使用内存 SQLite，不依赖外部服务；每个模块至少覆盖：成功路径、权限不足 403、未登录 401、不存在 404。
- 测试报告命名 `<module>-backend-test.md`，存放 `docs/tests/backend/`。

## Rulings（计划前置裁定）

1. **文档替代**：用户指定的 `docs/design/plans/rbac-authorization-plan.md`、`docs/design/db/ER_DESIGN_ANALYSIS.md` 不存在；以 `docs/design/plans/rbac-plan.md` + `docs/design/db/README.md`（ER 设计分析）+ `script.sql` 为准。
2. **直接授权不新增表**：审批通过后的权限授予不新增 `user_permissions` 表，改为「有效权限 = 角色权限 ∪ 已通过且未过期的申请」实时计算；到期即自然失效，无需回收任务。成本：每次鉴权多一次查询。
3. **dept 数据范围降级**：业务表无 `department_id`，`dept` 视图按 `created_by` 过滤（等价 own），字段与语义保留以便后续扩展。
4. **工具调用日志**：V3 §3.3.5 要求 `GET /tools/{id}/logs`，但库中无调用日志表；接口返回工具统计摘要 + 空日志分页，不新增表。
5. **审计 IP/UA**：由 `RequestContextMiddleware` 写入 contextvar，Service 层不接触 HTTP 对象。
6. **`created_by` 类型差异**：业务表 `created_by` 为 VARCHAR(100)（用户名），`users.created_by` 为 INTEGER（用户 ID），数据权限过滤按各自类型取值。

---

## File Structure（新增）

```
backend/app/
├── core/{request_context,data_scope,permission_catalog}.py
├── modules/role/{schema,repository,service,api}.py
├── modules/permission/{schema,repository,service,api}.py
├── modules/audit/{model,schema,repository,service,api}.py
├── modules/approval/{model,schema,repository,service,api}.py
├── modules/model/{model,schema,repository,service,api}.py
├── modules/agent/{model,schema,repository,service,api}.py
├── modules/prompt/{model,schema,repository,service,api}.py
├── modules/knowledge/{model,schema,repository,service,api}.py
├── modules/tool/{model,schema,repository,service,api}.py
├── modules/conversation/{model,schema,repository,service,api}.py
├── modules/dashboard/{schema,repository,service,api}.py
├── modules/analytics/{schema,repository,service,api}.py
├── modules/system/{model,schema,repository,service,api}.py
└── seed.py
backend/tests/test_{role,permission,audit,approval,model,agent,prompt,knowledge,tool,conversation,dashboard,analytics,system}.py
```

---

### Task 1: 核心能力增强

**Files:** `core/permission_catalog.py`、`core/request_context.py`、`core/data_scope.py`、`core/deps.py`（改）、`main.py`（改）
**Interfaces:**
- `PERMISSION_CATALOG: list[tuple[code, name, description]]`（71 条）。
- `RequestContextMiddleware`：`client_ip() -> str`、`user_agent() -> str`。
- `scope_condition(model, user, owner_field="created_by") -> ColumnElement | None`；`assert_in_scope(obj, user, owner_field) -> None`。
- `get_effective_permission_codes(db, user) -> set[str]`：角色权限 ∪ 有效审批授权；`get_current_user_with_permission(code)` 改为 async 依赖。

- [x] Step 1：实现上述文件，`pytest -q` 保持 22 passed
- [x] Step 2：commit

---

### Task 2: role / permission 模块

**Interfaces:**
- role：`GET /roles/`（登录）、`GET /roles/search`（role:list）、`GET /roles/{id}`（role:read）、`POST /roles`（role:create）、`PUT /roles/{id}`（role:update）、`DELETE /roles/{id}`（role:delete）、`PUT /roles/{id}/permissions`（role:assign_permissions）。
- permission：`GET /permissions/`（登录）、`GET /permissions/search`（permission:list）、`GET /permissions/{id}`（permission:read）、`POST /permissions`（permission:create）、`PUT /permissions/{id}`（permission:update，code 不可改）、`DELETE /permissions/{id}`（permission:delete）。
- 写操作记录审计（module=role/permission）。

- [x] Step 1：写 `tests/test_role.py`、`tests/test_permission.py` 并观察 RED
- [x] Step 2：实现 api/service/repository/schema，注册路由
- [x] Step 3：GREEN，commit

---

### Task 3: audit / approval 模块 + user 更新

**Interfaces:**
- `GET /system/audit-logs`（system:audit，支持 module/action/username 过滤 + 分页）、`GET /system/audit-logs/export`（CSV）。
- `POST /approvals/apply`（approval:apply）、`GET /approvals/my`（approval:apply）、`GET /approvals/list`（approval:audit）、`PUT /approvals/{id}/audit`（approval:audit）。
- 审批通过：status=approved，写 approver/approved_at/expired_at；`get_effective_permission_codes` 立即生效。
- `PUT /users/{id}`（user:update，可改 email/is_active/data_scope/密码）。

- [x] Step 1：写 `tests/test_audit.py`、`tests/test_approval.py`，RED
- [x] Step 2：实现并注册；user 写操作补审计
- [x] Step 3：GREEN，commit

---

### Task 4: model / agent / prompt 模块

**Interfaces（均按 V3 §3.3.5 权限码）：**
- 模型：`/models` CRUD（model:list/read/create/update/delete）、`/models/providers` CRUD（model:provider_manage）、`POST /models/providers/{id}/test` 与 `POST /models/{id}/test`（model:test）。路由顺序：`/providers` 先于 `/{model_id}`。
- Agent：`/agents` CRUD、`POST /agents/{id}/publish`（agent:publish，生成 agent_versions + 置 status=active）、`GET /agents/{id}/versions`（agent:read）、`POST /agents/{id}/versions/{version}/rollback`（agent:publish）、`POST /agents/{id}/test`（agent:test）、`GET /agents/{id}/monitor`（agent:monitor）。
- Prompt：`/prompts` CRUD、`POST /prompts/{id}/publish`、`GET /prompts/{id}/versions`、`POST /prompts/{id}/versions/{version}/rollback`、`POST /prompts/{id}/test`。

- [x] Step 1：三个测试文件 RED
- [x] Step 2：实现三模块（含版本表）
- [x] Step 3：GREEN，commit

---

### Task 5: knowledge / tool 模块

**Interfaces：**
- 知识库：`/knowledge-bases` CRUD；`POST /{id}/documents`（knowledge:document_upload，登记文档并置 processing→completed，按 chunk_size 生成 segments）、`GET /{id}/documents`、`POST /{id}/documents/{doc_id}/retry`、`DELETE /{id}/documents/{doc_id}`；`GET /{id}/segments`、`PUT/DELETE /{id}/segments/{seg_id}`；`POST /{id}/retrieval-test`（关键词打分返回 top_k）；`POST /{id}/reindex`。
- 工具：`/tools` CRUD、`POST /{id}/test`（tool:test）、`POST /{id}/toggle`（tool:toggle）、`GET /{id}/logs`（tool:read）。

- [x] Step 1：两个测试文件 RED
- [x] Step 2：实现两模块
- [x] Step 3：GREEN，commit

---

### Task 6: conversation / dashboard / analytics / system 模块

**Interfaces：**
- 对话：`GET /conversations`（conversation:list，status/agent 过滤）、`GET /{id}`、`GET /{id}/turns`、`GET /turns/{turn_id}/trace`、`POST /{id}/annotate`、`GET /{id}/export`（CSV）。
- 工作台：`/dashboard/{stats,trends,top-agents,recent-alerts,resource-usage}`（dashboard:read）。
- 统计：`/analytics/{overview,daily,by-agent,by-model,costs,evaluation}`（analytics:read）。
- 系统：`/system/api-keys` CRUD（system:api_keys）、`/system/alerts/rules` CRUD + `active` + `{id}/acknowledge` + `{id}/resolve`（system:alerts）、`/system/settings` GET/PUT（system:settings）。

- [x] Step 1：四个测试文件 RED
- [x] Step 2：实现四模块
- [x] Step 3：GREEN，commit

---

### Task 7: 种子数据 + 报告

**Files:** `backend/seed.py`、`docs/tests/backend/*.md`
- [x] Step 1：`seed.py` 写入 71 权限码 + 3 角色（授权关系对齐 init-data.sql）+ 3 演示账号 + 业务演示数据
- [x] Step 2：`pytest tests/ -q` 全绿
- [x] Step 3：按模块生成测试报告（含用例清单、执行命令、结果统计）
- [x] Step 4：commit

---

## Review Focus

1. 所有受保护接口在无权限用户下返回业务码 403，未登录 401。
2. 超管在任意业务接口放行。
3. 审批通过后权限立即生效；拒绝不生效；过期申请不再生效。
4. 数据权限：own 仅见本人（业务表按 username），all 见全量，越权详情/更新/删除 403。
5. 审计：写操作落库，读操作不落库；`audit_logs.user_id` 可空。
6. 版本/发布类接口幂等：重复 publish 生成新版本并置旧版本 is_current=false。
