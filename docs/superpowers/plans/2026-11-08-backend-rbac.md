# backend · RBAC 核心后端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans（inline）来逐任务实现。Step 用 checkbox（`- [ ]`）跟踪。

**Goal:** 在 `backend/` 下从零新建一个 Python + FastAPI + SQLAlchemy 后端，按「先分模块、模块内再分层（api/service/repository/model/schema）」实现 RBAC 核心（用户/角色/权限 + 认证/验证码 + 审计 + 审批），每个模块全部 API 经 pytest 单元测试，并产出 Markdown 测试报告。

**Architecture:** 复用 `chenguang-agent-platform-v4` 已验证的五层模式（`api.py → service.py → repository.py → model.py → schema.py`），但落地到 `backend/app/modules/<module>/`。数据库用 SQLite（文件 `backend/rbac.db`，测试用内存库），表结构与 `docs/design/db/script.sql` 一致。授权沿用 `get_current_user` + `get_current_user_with_permission(permission_code)` 白盒模式。

**Tech Stack:** Python 3.14 + FastAPI + SQLAlchemy 2.0（async）+ Pydantic v2 + PyJWT + bcrypt；pytest + pytest-asyncio + httpx（测试）。

**Spec:** `docs/spec/PROJECT_SPEC_V3.md`（RBAC 授权需求增量，§2~§3）+ `docs/design/db/script.sql`（表结构）+ `docs/design/db/init-data.sql`（种子数据）。

## Global Constraints

- 后端全部代码在 `backend/` 下；模块路径 `backend/app/modules/<module>/{api,service,repository,model,schema}.py`。
- 权限码格式 `模块:操作` 全小写；核心 27 个（V2 22 + V3 5：`data_scope:own/dept/all`、`approval:apply/audit`）。
- 超管 `is_superuser` 直接放行；权限不足 `BizException(code=403, message="没有权限执行该操作")`，全局处理器返回 HTTP 200 + 业务码。
- 响应统一 `{"code":200,"message":"success","data":...}`；分页 `PageResult{items,total,page,page_size}`。
- 数据库连接串从环境变量读取，SQLite 默认；配置 fail-fast（缺必填启动即报错）。
- 每个模块的测试报告命名 `【模块名]-backend-test.md`，存 `docs/tests/backend/`。
- 所有 API 必须经单元测试；测试用内存 SQLite（`sqlite+aiosqlite:///:memory:`），不依赖外部服务。

## Review Focus

1. 无任何角色/权限的用户访问受保护接口 → 403（而非空集报错）。
2. 超管即使角色不含某权限码也放行。
3. `/users/me/permissions` 去重且排序；超管返回全部已定义权限码（从库实时推导）。
4. 三个全量列举接口（`GET /users`、`/roles/`、`/permissions/`）只需登录、无需权限码。
5. 用户删除后审计日志仍保留（`audit_logs.user_id` 可空）。
6. 权限申请审批通过后权限立即生效；拒绝不生效。

---

## File Structure

```
backend/
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                  # create_app + lifespan + 路由注册 + 异常处理器
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Settings(pydantic-settings)
│   │   ├── database.py          # async engine + async_sessionmaker + get_db
│   │   ├── base_model.py        # Base + TimestampMixin + BaseModel(id/created_at/updated_at)
│   │   ├── base_repository.py   # BaseRepository[T]：get_by_id/get_all/get_page/create/update/delete
│   │   ├── base_schema.py       # ResponseSchema[T] + PageResult[T]
│   │   ├── deps.py              # get_db / get_current_user / get_current_user_with_permission
│   │   ├── exceptions.py        # BizException + register_exception_handlers
│   │   └── security.py          # hash_password / verify_password / create_token / decode_token
│   └── modules/
│       ├── auth/                # 登录/验证码（api/service/schema；无 model/repository）
│       ├── user/                # 用户 CRUD + 分配角色 + 当前用户权限
│       ├── role/                # 角色 CRUD + 分配权限
│       ├── permission/          # 权限 CRUD
│       ├── audit/               # 审计日志（只读查询 + 写操作切面）
│       └── approval/            # 权限申请/审批
└── tests/
    ├── __init__.py
    ├── conftest.py              # app + db_session + client fixture（内存库）
    ├── test_auth.py
    ├── test_user.py
    ├── test_role.py
    ├── test_permission.py
    ├── test_audit.py
    └── test_approval.py
```

---

### Task 1: 项目骨架 + core 基础设施

**Files:** `backend/requirements.txt`、`backend/.env.example`、`backend/app/__init__.py`、`backend/app/core/{__init__,config,database,base_model,base_repository,base_schema,exceptions,security}.py`、`backend/app/main.py`、`backend/tests/{__init__,conftest}.py`

**Interfaces:**
- `Settings`（pydantic-settings）：`DATABASE_URL`（默认 `sqlite+aiosqlite:///./rbac.db`）、`JWT_SECRET`、`JWT_EXPIRES_MINUTES`、`APP_NAME`。
- `BaseModel`：`id`（INTEGER 自增，SQLite 用 Integer）、`created_at`、`updated_at`（server_default=func.now()）。
- `BaseRepository[T]`：`get_by_id`、`get_all(offset,limit)`、`get_page(offset,limit,keyword,search_fields)`、`create`、`update`、`delete`、`delete_by_id`。
- `ResponseSchema[T]`（code=200/message="success"/data=None）、`PageResult[T]`（items/total/page/page_size）。
- `BizException(code,message)`；`register_exception_handlers(app)`。
- `hash_password`/`verify_password`（bcrypt）、`create_token(sub)`/`decode_token(token)`（PyJWT）。
- `get_db()`（async generator）、`get_current_user(token,db)`、`get_current_user_with_permission(permission_code)`。

- [ ] Step 1：写 `requirements.txt`、`.env.example`、`core/*`、`main.py`、`tests/conftest.py`（含 app + 内存库 fixture 与 health 测试）
- [ ] Step 2：`pytest tests/ -q` 预期 health 测试 PASS
- [ ] Step 3：commit

---

### Task 2: 认证模块（auth）—— 登录 + 验证码

**Files:** `backend/app/modules/auth/{__init__,api,service,schema}.py`、`backend/app/modules/auth/`、`backend/tests/test_auth.py`

**Interfaces:**
- `POST /api/v1/auth/login`：`{username,password}` → `{token,user}`；密码错/用户不存在 → 401。
- 登录成功写 `audit_logs`（module="auth", action="login"）。

- [ ] Step 1：写失败测试（test_auth.py：登录成功/密码错误/用户不存在）
- [ ] Step 2：RED
- [ ] Step 3：实现 auth 模块 + 在 main.py 注册
- [ ] Step 4：GREEN
- [ ] Step 5：commit

---

### Task 3: 用户模块（user）

**Files:** `backend/app/modules/user/{__init__,model,schema,repository,service,api}.py`、`backend/tests/test_user.py`

**Interfaces:**
- `GET /users`（登录即可）→ 全量列表
- `GET /users/search`（`user:list`）→ 分页搜索
- `GET /users/{id}`（`user:read`）
- `POST /users`（`user:create`）
- `DELETE /users/{id}`（`user:delete`）
- `PUT /users/{id}/roles`（`user:assign_roles`）
- `GET /users/{id}/roles`（`user:read_roles`）
- `GET /users/me`（登录）
- `GET /users/me/permissions`（登录）→ 去重排序权限码

- [ ] Step 1：写失败测试（全接口 + 403/401 分支）
- [ ] Step 2：RED
- [ ] Step 3：实现五层 + 注册
- [ ] Step 4：GREEN
- [ ] Step 5：commit

---

### Task 4: 角色模块（role）

**Files:** `backend/app/modules/role/{__init__,model,schema,repository,service,api}.py`、`backend/tests/test_role.py`

**Interfaces:** `GET /roles/`（登录）、`GET /roles/search`（`role:list`）、`GET /roles/{id}`（`role:read`）、`POST /roles`（`role:create`）、`PUT /roles/{id}`（`role:update`）、`DELETE /roles/{id}`（`role:delete`）、`PUT /roles/{id}/permissions`（`role:assign_permissions`）。

- [ ] Step 1~5：同 Task 3 流程

---

### Task 5: 权限模块（permission）

**Files:** `backend/app/modules/permission/{...}.py`、`backend/tests/test_permission.py`

**Interfaces:** `GET /permissions/`（登录）、`GET /permissions/search`（`permission:list`）、`GET /permissions/{id}`（`permission:read`）、`POST /permissions`（`permission:create`）、`PUT /permissions/{id}`（`permission:update`）、`DELETE /permissions/{id}`（`permission:delete`）。

- [ ] Step 1~5：同 Task 3 流程

---

### Task 6: 审计模块（audit）

**Files:** `backend/app/modules/audit/{__init__,model,schema,repository,service,api}.py`、`backend/tests/test_audit.py`

**Interfaces:** `GET /audit-logs`（`system:audit`）→ 分页查询；`audit` 写操作切面（在 service 层记录 create/update/delete/assign/approve 等）。

- [ ] Step 1~5：同 Task 3 流程

---

### Task 7: 审批模块（approval）

**Files:** `backend/app/modules/approval/{...}.py`、`backend/tests/test_approval.py`

**Interfaces:** `POST /approvals/apply`（`approval:apply`）、`GET /approvals/my`（`approval:apply`）、`GET /approvals/list`（`approval:audit`）、`PUT /approvals/{id}/audit`（`approval:audit`，通过后授予权限码）。

- [ ] Step 1~5：同 Task 3 流程

---

### Task 8: 种子数据 + 测试报告汇总

**Files:** `backend/seed.py`（或 `app/core/seed.py`）、`docs/tests/backend/{auth,user,role,permission,audit,approval}-backend-test.md`

- [ ] Step 1：写 seed 脚本（27 核心权限码 + 3 角色 + 3 用户 + 授权关系，对齐 init-data.sql）
- [ ] Step 2：跑全量测试 `pytest tests/ -q` 全绿
- [ ] Step 3：生成 6 份测试报告
- [ ] Step 4：commit

---

## Self-Review

**Spec 覆盖：** V3 §3.1（授权依赖）→ Task 1；§3.2（/users/me/permissions）→ Task 3；§3.5（审计）→ Task 6；§3.6（审批）→ Task 7；用户/角色/权限 CRUD + 拦截 → Task 3/4/5。数据权限 `data_scope` 字段与过滤逻辑 → Task 3（user 模块的 list 接口按 data_scope 过滤，第一期实现 `own/all`，`dept` 需部门字段，本期仅存字段不启用）。

**类型一致性：** `get_current_user_with_permission` 在 Task 1 定义，Task 3/4/5/6/7 消费；`BaseRepository.get_page` 在 Task 1 定义，各模块 repository 复用。

**比例：** 计划以签名、接口清单、测试断言为主，不含完整函数体转录。
