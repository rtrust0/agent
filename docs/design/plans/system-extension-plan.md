# 系统管理扩展（API Key / 审计日志 / 告警规则 / 系统配置）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从零新建后端系统管理扩展四个独立子模块：API Key（`api_key/`）、审计日志（`audit_log/`）、告警规则与活跃告警（`alert_rule/`）、系统配置（`system_settings/`），各含完整五层实现，并挂载到 `/api/v1/system/*` 下受权限码拦截。

**Architecture:** 在 `src/modules/` 下新建 4 个独立子模块目录，与现有 `user/role/permission` 目录风格一致（每目录 `model.py/schema.py/repository.py/service.py/api.py` + 空 `__init__.py`）。四个子模块彼此独立，仅共享：`src/core/deps.py` 新增的 `get_current_user_with_permission` 权限拦截依赖，以及 `test/conftest.py` 的 aiosqlite 内存库 fixture。告警模块同时维护 `alert_rules`（规则）与 `alerts`（活跃/历史告警）两张表。

**Tech Stack:** Python 3.13 + FastAPI 0.135 + SQLAlchemy 2.0 async（本地 aiosqlite、生产 asyncmy）+ Pydantic v2 + Alembic + pytest 9 + pytest-asyncio 1.3（测试用 aiosqlite 内存库）。

**Spec:**
- 项目说明 V1：`docs/PROJECT_SPEC.md`
- 项目说明 V2（RBAC 授权）：`docs/spec/PROJECT_SPEC_V2.md`（§2.4 权限码、§2.5.1 权限拦截依赖）
- 模块设计文档：`app/docs/09-系统管理.md`（三/四/五/六节）
- API 接口规范（系统管理节）：`app/docs/10-API接口规范.md`
- 前端类型（字段权威来源）：`app/src/services/types/system.ts`
- 前端页面（实际消费方，仅参考）：`app/src/pages/system/ApiKeys.tsx`、`Audit.tsx`、`Alerts.tsx`、`Settings.tsx`

## Global Constraints

以下项目级约束对所有 Task 隐式生效，逐条精确值：

1. 路由统一 `/api/v1` 前缀；本计划 4 个 router 前缀分别为 `/system/api-keys`、`/system/audit-logs`、`/system/alerts`、`/system/settings`，均在 `src/main.py` 用 `app.include_router(..., prefix="/api/v1")` 注册，最终完整路径为 `/api/v1/system/...`。
2. 响应统一 `ResponseSchema(code=200, message="success", data=...)`（`src/core/base_schema.py`）；分页统一 `PageResult(items, total, page, page_size)`。
3. 分页参数 `PageParams(page 从1起, page_size 默认10 上限100, keyword)`（`src/core/deps.py`），通过 `Depends()` 注入；`offset = (page-1)*page_size`。**测试中构造分页参数须三个参数都显式传**：`PageParams(page=1, page_size=10, keyword=None)`（否则 `page`/`keyword` 会取到 FastAPI 的 `Query` 默认对象而非值）。
4. 业务异常抛 `BizException(code, message)`（`src/core/exceptions.py`），全局异常处理器返回 HTTP 200 + `{"code":..., "message":..., "data":null}`。
5. 授权：本计划 4 模块的所有接口均挂 `Depends(get_current_user_with_permission("<perm>"))`，权限码分别为 `system:api_keys`、`system:audit`、`system:alerts`、`system:settings`（来源 PROJECT_SPEC_V2 §2.4）。超管 `User.is_superuser == True` 直接放行；无权限抛 `BizException(code=403, message="没有权限执行该操作")`。
6. ORM 继承 `BaseModel`（`src/core/base_model.py`，含自增 `BigInteger id`、`created_at`、`updated_at`）；JSON 列用 `mapped_column(JSON)`；外键/状态/枚举一律存字符串（无 FK 关联，与前端 `string` 类型一致）。各模块表名：`api_keys`、`audit_logs`、`alert_rules`、`alerts`、`system_settings`。
7. 后端表字段/ORM/Pydantic 均用 snake_case；JSON 列内部键用 camelCase（与前端嵌套类型逐字一致）。字段映射（前端 `types/system.ts` 权威，类型一一对应）：

   **ApiKey**：`id:string`→`id:int`、`name`→`name:str`、`key`→`key:str`（创建返回完整，列表/详情脱敏）、`permissions:'all'|'readonly'|'agent_only'`→`permissions:str`、`status:'active'|'disabled'|'expired'`→`status:str`、`rateLimit:number`→`rate_limit:int`、`callCount:number`→`call_count:int`、`lastUsedAt:string`→`last_used_at:datetime|None`、`createdBy:string`→`created_by:str|None`、`createdAt:string`→`created_at:datetime`；设计文档 09 增补 `allowedAgentIds:string[]|'all'`→`allowed_agent_ids:list[str]|str|None`(JSON)、`expiresAt?:string`→`expires_at:datetime|None`。

   **AuditLog**：`userId:string`→`user_id:str`、`username:string`→`username:str`、`action:'create'|'update'|'delete'|'publish'|'login'|'logout'|'config'|'upload'`→`action:str`、`module:'agent'|'model'|'prompt'|'knowledge'|'tool'|'system'|'user'`→`module:str`、`targetId?:string`→`target_id:str|None`、`targetName?:string`→`target_name:str|None`、`detail:string`→`detail:str(Text)`、`ipAddress:string`→`ip_address:str`、`createdAt:string`→`created_at:datetime`；设计文档 09 增补 `userAgent:string`→`user_agent:str|None`。

   **AlertRule**：`name`→`name:str`、`description`→`description:str|None`、`condition{metric,operator:'gt'|'lt'|'eq'|'gte'|'lte',threshold,duration,scope?}`→`condition:dict`(JSON)、`notification{channels:('email'|'webhook'|'sms')[],recipients:string[]}`→`notification:dict|None`(JSON)、`status:'enabled'|'disabled'`→`status:str`、`createdBy`→`created_by:str|None`、`createdAt/updatedAt`→`created_at/updated_at:datetime`。

   **Alert（活跃告警，取 `SystemAlert` 类型）**：`type:'error'|'warning'|'info'`→`type:str`、`title`→`title:str`、`message`→`message:str(Text)`、`source`→`source:str`、`severity:'low'|'medium'|'high'|'critical'`→`severity:str`、`status:'active'|'acknowledged'|'resolved'`→`status:str`、`count:number`→`count:int`、`firstOccurredAt`→`first_occurred_at:datetime`、`lastOccurredAt`→`last_occurred_at:datetime`、`acknowledgedBy:string|null`→`acknowledged_by:str|None`、`acknowledgedAt?:string`→`acknowledged_at:datetime|None`、`resolvedAt?:string`→`resolved_at:datetime|None`。

   **SystemSettings**：`systemName`→`system_name:str`、`systemDescription`→`system_description:str|None`、`defaultLanguage`→`default_language:str`、`defaultModel`→`default_model:str`、`defaultTemperature:number`→`default_temperature:float`、`defaultMaxTokens:number`→`default_max_tokens:int`、`smtpServer`→`smtp_server:str|None`、`smtpPort:number`→`smtp_port:int`、`senderEmail`→`sender_email:str|None`。

8. **字段命名权威与前端不一致提示**：`types/system.ts`（本计划权威源）与 `app/src/services/mock/data/system.ts`、部分页面组件存在字段漂移（如 ApiKey 用 `callCount` 而页面 `ApiKeys.tsx` 读 `usageCount`；AuditLog 用 `username`/`createdAt`/`targetName` 而页面 `Audit.tsx` 读 `userName`/`timestamp`/`resourceName`；`types/system.ts` 中另有未被页面消费的 `ActiveAlert` 接口）。本计划一律以 `types/system.ts` 为准；前端 mock/页面字段对齐属前端工作，不在本计划范围。
9. 默认值（来源 `app/docs/09-系统管理.md` 六、系统配置）：`system_name="辰光Agent平台"`、`default_language="zh-CN"`、`default_model="GPT-4"`、`default_temperature=0.7`、`default_max_tokens=4096`、`smtp_port=587`。
10. 业务错误码：`47001`「API Key 不存在」、`47002`「告警规则不存在」、`47003`「告警不存在」、`47004`「仅活跃告警可确认」、`47005`「告警已解决」。
11. 测试：pytest + `@pytest.mark.asyncio`（无 pytest.ini，逐测试加装饰器）；测试文件放 `/test/`；DB 测试用 aiosqlite 内存库 fixture `db_session`（`test/conftest.py`，`poolclass=StaticPool`）。命令 `pytest test/xxx.py::test_name -v`。
12. 提交消息中文摘要（各 Task 末）。每步 commit 附 `Co-Authored-By: Claude Code <noreply@anthropic.com>`。

## Review Focus

以下 5 类输入/边界最易踩坑，逐条对应到所属 Task 的测试：

1. API Key 完整密钥泄露：创建仅返回一次完整 `full_key`，列表/详情必须脱敏（`sk-` + 前缀到第一个 `-` + 20 个 `*` + 后 6 位），否则泄漏敏感凭证。→ Task 2 `test_create_returns_full_key_once_and_list_masks`。
2. 过期 API Key 状态：`expires_at < now` 的 key 读取时 `status` 必须报告为 `expired`（即使 DB 存 `active`），否则已过期密钥仍被当活跃用。→ Task 2 `test_expired_key_reported_as_expired`。
3. 审计日志空结果：无匹配记录返回 `total=0, items=[]`（非 500）；`action`/`module` 传未知值安全返回空结果而非 500。→ Task 3 `test_list_audit_logs_empty_result`。
4. 告警确认/解决非法状态：对不存在告警 id 抛 `BizException(47003)`；对非 `active` 告警 `acknowledge` 抛 `47004`、对已 `resolved` 告警 `resolve` 抛 `47005`，不能静默成功产生脏数据。→ Task 4 `test_acknowledge_missing_alert`、`test_acknowledge_resolved_alert_fails`、`test_resolve_already_resolved_fails`。
5. 系统配置单行唯一性 + 整体更新：GET 在无配置行时返回默认值（非 500）；PUT 整体覆盖（非合并），缺必填字段（如 `system_name`）由 Pydantic 拒绝为 422。→ Task 5 `test_get_settings_creates_defaults`、`test_update_settings_overwrites`。

---

## File Structure

- Create: `src/modules/api_key/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py` — API Key 五层（含 key 生成/脱敏纯函数）
- Create: `src/modules/audit_log/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py` — 审计日志五层（只读：列表 + CSV 导出）
- Create: `src/modules/alert_rule/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py` — 告警五层（`alert_rules` + `alerts` 两表）
- Create: `src/modules/system_settings/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py` — 系统配置五层（单行表）
- Modify: `src/core/deps.py` — 新增 `has_permission` + `get_current_user_with_permission`
- Modify: `src/main.py` — 导入并注册 4 个 router
- Modify: `alembic/env.py` — 追加 4 个 model 导入
- Create: `alembic/versions/<hash>_系统管理扩展5表.py` — 迁移（autogenerate）
- Create: `test/conftest.py` — aiosqlite 内存库 `db_session` fixture（Task 2 创建，后续复用）
- Test: `test/test_permission_dep.py`、`test/test_api_key.py`、`test/test_audit_log.py`、`test/test_alert_rule.py`、`test/test_system_settings.py`

---

### Task 1: 权限拦截依赖 `get_current_user_with_permission`

**Files:**
- Modify: `src/core/deps.py`
- Test: `test/test_permission_dep.py`

**Interfaces:**
- Consumes: `User`（`src/modules/user.model`，含 `is_superuser: bool`、`roles: list[Role]` lazy=selectin）、`Role.permissions: list[Permission]`（lazy=selectin）、`Permission.code: str`（`src/modules/permission.model`）；`get_current_user`（`src/core/deps.py` 已存在）；`BizException`。
- Produces:
  - `def has_permission(user: User, permission_code: str) -> bool`（纯函数，可脱离 DB 测试）
  - `def get_current_user_with_permission(permission_code: str)` — 返回一个 FastAPI 依赖；内部复用 `Depends(get_current_user)` 取用户，再调 `has_permission`；无权限抛 `BizException(code=403, message="没有权限执行该操作")`，有权限返回 `User`。

- [ ] **Step 1: 写失败测试**

在 `test/test_permission_dep.py` 写 3 个测试（纯函数，不依赖 DB）：

```python
from src.core.deps import has_permission
from src.modules.user.model import User
from src.modules.role.model import Role
from src.modules.permission.model import Permission

def _make_user(codes=None, superuser=False):
    if superuser:
        return User(is_superuser=True, roles=[])
    return User(is_superuser=False, roles=[Role(permissions=[Permission(code=c) for c in (codes or [])])])

def test_superuser_has_all_permissions():
    assert has_permission(_make_user(superuser=True), "anything:at_all") is True

def test_user_with_permission_passes():
    assert has_permission(_make_user(["system:api_keys"]), "system:api_keys") is True

def test_user_without_permission_denied():
    assert has_permission(_make_user(["system:api_keys"]), "system:alerts") is False
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_permission_dep.py::test_superuser_has_all_permissions -v`
Expected: FAIL，`ImportError: cannot import name 'has_permission' from 'src.core.deps'`

- [ ] **Step 3: 实现 `has_permission` 与 `get_current_user_with_permission` 于 `src/core/deps.py`**

`has_permission`：超管直接 `True`；否则遍历 `user.roles` → `role.permissions` 收集 `perm.code` 到 `set`，返回 `permission_code in codes`。`get_current_user_with_permission(permission_code)` 返回内层 `async def _require(user: User = Depends(get_current_user)) -> User`，内部 `if not has_permission(user, permission_code): raise BizException(code=403, message="没有权限执行该操作")`，否则 `return user`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_permission_dep.py -v`
Expected: PASS（3 个测试全绿）

- [ ] **Step 5: Commit**

```bash
git add src/core/deps.py test/test_permission_dep.py
git commit -m "feat: 系统管理权限拦截依赖"
```

---

### Task 2: API Key 子模块

**Files:**
- Create: `src/modules/api_key/__init__.py`
- Create: `src/modules/api_key/model.py`
- Create: `src/modules/api_key/schema.py`
- Create: `src/modules/api_key/repository.py`
- Create: `src/modules/api_key/service.py`
- Create: `src/modules/api_key/api.py`
- Create: `test/conftest.py`
- Modify: `src/main.py`
- Test: `test/test_api_key.py`

**Interfaces:**
- Consumes: Task 1 `get_current_user_with_permission`；`BaseModel`；`BaseRepository[T]`（`get_by_id`/`create`/`update`/`delete`/`get_page`）；`PageParams`/`PageResult`/`ResponseSchema`/`BizException`；`get_db`。
- Produces:
  - `class ApiKey(BaseModel)`：`__tablename__ = "api_keys"`，字段 `name: str(String(100))`、`key: str(String(100), unique, index)`、`permissions: str(String(20), default="all")`、`status: str(String(20), default="active")`、`rate_limit: int(Integer, default=60)`、`call_count: int(Integer, default=0)`、`last_used_at: datetime | None`、`expires_at: datetime | None`、`allowed_agent_ids: list | str | None(JSON)`、`created_by: str | None(String(100))`。
  - `class ApiKeyCreate(BaseModel)`：`name: str`、`permissions: Literal["all","readonly","agent_only"] = "all"`、`rate_limit: int = 60`、`allowed_agent_ids: list[str] | str | None = None`、`expires_at: datetime | None = None`。
  - `class ApiKeyUpdate(BaseModel)`：`name: str|None=None`、`permissions: ...|None=None`、`rate_limit: int|None=None`、`allowed_agent_ids: list[str]|str|None=None`、`expires_at: datetime|None=None`、`status: Literal["active","disabled","expired"]|None=None`。
  - `class ApiKeyRead(BaseModel)`（`model_config = {"from_attributes": True}`）：`id:int`、`name:str`、`key:str`、`permissions:str`、`status:str`、`rate_limit:int`、`call_count:int`、`last_used_at:datetime|None`、`expires_at:datetime|None`、`allowed_agent_ids:list[str]|str|None`、`created_by:str|None`、`created_at:datetime`（无 `updated_at`，与前端 `ApiKey` 类型一致）。
  - `class ApiKeyCreated(BaseModel)`：`api_key: ApiKeyRead`、`full_key: str`。
  - `def generate_api_key() -> str`（模块级纯函数，`"sk-" + secrets.token_urlsafe(24)`，长度 ≥ 32）。
  - `def mask_api_key(full: str) -> str`（模块级纯函数，`f"{full.split('-')[0]}-" + "*"*20 + full[-6:]`）。
  - `class ApiKeyRepository(BaseRepository[ApiKey])`：`SEARCH_FIELDS = ["name"]`；`async def search_page(self, offset: int, limit: int, keyword: str | None, status: str | None = None) -> tuple[list[ApiKey], int]`。
  - `class ApiKeyService`：`__init__(self, db: AsyncSession)`；`async def create_api_key(self, data: ApiKeyCreate, current_user: str | None) -> ApiKeyCreated`；`async def list_api_keys(self, params: PageParams, status: str | None = None) -> PageResult[ApiKeyRead]`；`async def update_api_key(self, api_key_id: int, data: ApiKeyUpdate) -> ApiKeyRead`（不存在抛 `47001`）；`async def delete_api_key(self, api_key_id: int) -> None`（不存在抛 `47001`）；内部 `_to_read(self, key: ApiKey) -> ApiKeyRead`。
  - `router = APIRouter(prefix="/system/api-keys", tags=["系统管理"])` 与 `def get_api_key_service(db: AsyncSession = Depends(get_db)) -> ApiKeyService`。

- [ ] **Step 1: 写失败测试（模型 + 纯函数 + conftest）**

在 `test/conftest.py` 写 `db_session` fixture（`@pytest_asyncio.fixture`）：

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.core.base_model import Base

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()
```

在 `test/test_api_key.py` 写 `test_api_key_model_registered`、`test_generate_api_key_format`、`test_mask_api_key`：

```python
from src.modules.api_key.model import ApiKey
from src.modules.api_key.service import generate_api_key, mask_api_key
from src.core.base_model import BaseModel

def test_api_key_model_registered():
    assert ApiKey.__tablename__ == "api_keys"
    assert issubclass(ApiKey, BaseModel)
    assert hasattr(ApiKey, "rate_limit") and hasattr(ApiKey, "call_count")

def test_generate_api_key_format():
    k = generate_api_key()
    assert k.startswith("sk-") and len(k) >= 32

def test_mask_api_key():
    assert mask_api_key("sk-prod-aaaaaaaaaabbbbbb") == "sk-prod-" + "*" * 20 + "bbbbbb"
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_api_key.py::test_api_key_model_registered -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'src.modules.api_key'`

- [ ] **Step 3: 实现 `model.py` + 纯函数（暂先放 `service.py`）+ `__init__.py`**

按 Produces 写 `ApiKey` ORM（`allowed_agent_ids` 用 `mapped_column(JSON, nullable=True)`；`key` 加 `unique=True, index=True`）。在 `service.py` 先实现 `generate_api_key`（`secrets.token_urlsafe(24)`）与 `mask_api_key`。创建空 `__init__.py`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_api_key.py::test_api_key_model_registered test/test_api_key.py::test_generate_api_key_format test/test_api_key.py::test_mask_api_key -v`
Expected: PASS

- [ ] **Step 5: 写失败测试（schema）**

在 `test/test_api_key.py` 追加：

```python
import pytest
from pydantic import ValidationError
from src.modules.api_key.schema import ApiKeyCreate, ApiKeyRead

def test_api_key_create_permissions_literal():
    assert ApiKeyCreate(name="prod", permissions="agent_only").permissions == "agent_only"
    with pytest.raises(ValidationError):
        ApiKeyCreate(name="bad", permissions="admin")

def test_api_key_read_from_attributes():
    from datetime import datetime
    read = ApiKeyRead.model_validate(
        ApiKey(id=1, name="prod", key="sk-abc123", permissions="all", status="active",
               rate_limit=60, call_count=0, last_used_at=None, expires_at=None,
               allowed_agent_ids=None, created_by="admin",
               created_at=datetime(2024, 2, 7, 10, 0)))
    assert read.call_count == 0 and read.status == "active"
```

- [ ] **Step 6: 运行确认失败 → 实现 `schema.py` → 运行确认通过**

Run: `pytest test/test_api_key.py::test_api_key_create_permissions_literal -v` → FAIL（schema 未建）。实现 `src/modules/api_key/schema.py`（按 Produces 五个模型，`ApiKeyRead` 加 `from_attributes`）。再 Run 上述两个测试 → PASS。

- [ ] **Step 7: 写失败测试（repository）**

```python
import pytest
from src.modules.api_key.repository import ApiKeyRepository
from src.modules.api_key.model import ApiKey

@pytest.mark.asyncio
async def test_search_page_status_filter(db_session):
    repo = ApiKeyRepository(db_session)
    await repo.create(ApiKey(name="a", key="sk-aaa", status="active"))
    await repo.create(ApiKey(name="b", key="sk-bbb", status="disabled"))
    items, total = await repo.search_page(0, 20, None, status="disabled")
    assert total == 1 and items[0].name == "b"
```

- [ ] **Step 8: 运行确认失败 → 实现 `repository.py` → 运行确认通过**

Run: `pytest test/test_api_key.py::test_search_page_status_filter -v` → FAIL（repository 未建）。实现 `ApiKeyRepository`：`search_page` 基于 `select(ApiKey)`，`keyword` 复用 `get_page(search_fields=self.SEARCH_FIELDS)`，`status` 非空时叠加 `where(ApiKey.status == status)`，总数 `func.count()` 子查询，按 `id.asc()`，返回 `(items, total)`。再 Run → PASS。

- [ ] **Step 9: 写失败测试（service）**

```python
import pytest
from datetime import datetime, timedelta
from src.core.exceptions import BizException
from src.core.deps import PageParams
from src.modules.api_key.service import ApiKeyService
from src.modules.api_key.schema import ApiKeyCreate

@pytest.mark.asyncio
async def test_create_returns_full_key_once_and_list_masks(db_session):
    svc = ApiKeyService(db_session)
    created = await svc.create_api_key(ApiKeyCreate(name="prod"), current_user="admin")
    assert created.full_key.startswith("sk-")
    page = await svc.list_api_keys(PageParams(page=1, page_size=10, keyword=None))
    assert page.total == 1
    assert page.items[0].key != created.full_key
    assert page.items[0].key.endswith(created.full_key[-6:])

@pytest.mark.asyncio
async def test_expired_key_reported_as_expired(db_session):
    svc = ApiKeyService(db_session)
    await svc.create_api_key(ApiKeyCreate(name="old", expires_at=datetime.now() - timedelta(days=1)), current_user="admin")
    page = await svc.list_api_keys(PageParams(page=1, page_size=10, keyword=None))
    assert page.items[0].status == "expired"

@pytest.mark.asyncio
async def test_delete_missing_key_raises(db_session):
    svc = ApiKeyService(db_session)
    with pytest.raises(BizException) as e:
        await svc.delete_api_key(999)
    assert e.value.code == 47001
```

- [ ] **Step 10: 运行确认失败 → 实现 `service.py` → 运行确认通过**

Run: `pytest test/test_api_key.py::test_create_returns_full_key_once_and_list_masks -v` → FAIL（service 未建）。实现 `ApiKeyService`：`create_api_key` 生成 `full = generate_api_key()` 存库，返回 `ApiKeyCreated(api_key=_to_read(created), full_key=full)`；`_to_read` 中 `key=mask_api_key(api_key.key)`，且当 `expires_at` 存在且早于 `datetime.now()` 时 `status="expired"`；`update`/`delete` 先 `get_by_id`，不存在抛 `47001`。再 Run 3 个测试 → PASS。

- [ ] **Step 11: 写失败测试（api 路由）→ 实现 `api.py` + 注册 `main.py` → 运行确认通过**

在 `test/test_api_key.py` 追加：

```python
from src.modules.api_key.api import router

def test_api_key_routes_registered():
    paths = {r.path for r in router.routes}
    assert "/system/api-keys" in paths
    assert "/system/api-keys/{api_key_id}" in paths
```

实现 `api.py`：`router = APIRouter(prefix="/system/api-keys", tags=["系统管理"])`；`GET ""`（`status: str | None = None` 查询参数 + `PageParams`）→ `ResponseSchema[PageResult[ApiKeyRead]]`；`POST ""` → `ResponseSchema[ApiKeyCreated]`；`PUT "/{api_key_id}"` → `ResponseSchema[ApiKeyRead]`；`DELETE "/{api_key_id}"` → `ResponseSchema`。每个路由加 `_: User = Depends(get_current_user_with_permission("system:api_keys"))`。在 `src/main.py` 导入 `router` 并 `app.include_router(router, prefix="/api/v1")`。

Run: `pytest test/test_api_key.py::test_api_key_routes_registered -v` → PASS。再 `python -c "from src.main import app"` 确认无导入错误。

- [ ] **Step 12: Commit**

```bash
git add src/modules/api_key/ test/test_api_key.py test/conftest.py src/main.py
git commit -m "feat: API Key子模块五层实现"
```

---

### Task 3: 审计日志子模块

**Files:**
- Create: `src/modules/audit_log/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py`
- Modify: `src/main.py`
- Test: `test/test_audit_log.py`

**Interfaces:**
- Consumes: Task 1 `get_current_user_with_permission`；Task 2 `db_session` fixture；`BaseModel`/`BaseRepository`/`PageParams`/`PageResult`/`ResponseSchema`/`BizException`/`get_db`。
- Produces:
  - `class AuditLog(BaseModel)`：`__tablename__ = "audit_logs"`，字段 `user_id: str(String(50))`、`username: str(String(100))`、`action: str(String(20))`、`module: str(String(30))`、`target_id: str | None(String(50))`、`target_name: str | None(String(200))`、`detail: str(Text)`、`ip_address: str(String(50))`、`user_agent: str | None(String(300))`。**只增不改不删：service/repository 不提供 update/delete。**
  - `class AuditLogFilter(BaseModel)`：`user_id: str|None=None`、`action: str|None=None`、`module: str|None=None`、`start_time: datetime|None=None`、`end_time: datetime|None=None`（筛选字段为宽松字符串，未知值安全返回空结果）。
  - `class AuditLogRead(BaseModel)`（`from_attributes`）：`id:int`、`user_id:str`、`username:str`、`action:str`、`module:str`、`target_id:str|None`、`target_name:str|None`、`detail:str`、`ip_address:str`、`user_agent:str|None`、`created_at:datetime`。
  - `def audit_logs_to_csv(logs: list[AuditLog]) -> str`（模块级纯函数，表头 `时间,用户,操作,模块,对象,详情,IP地址`，行按该顺序取值）。
  - `class AuditLogRepository(BaseRepository[AuditLog])`：`async def filtered_page(self, offset: int, limit: int, keyword: str | None, filters: AuditLogFilter) -> tuple[list[AuditLog], int]`；`async def filtered_all(self, filters: AuditLogFilter) -> list[AuditLog]`。
  - `class AuditLogService`：`__init__(self, db: AsyncSession)`；`async def list_logs(self, params: PageParams, filters: AuditLogFilter) -> PageResult[AuditLogRead]`；`async def export_csv(self, filters: AuditLogFilter) -> str`。
  - `router = APIRouter(prefix="/system/audit-logs", tags=["系统管理"])` 与 `def get_audit_log_service(db: AsyncSession = Depends(get_db)) -> AuditLogService`。

- [ ] **Step 1: 写失败测试（模型 + CSV 纯函数）**

在 `test/test_audit_log.py` 写 `test_audit_log_model_registered`、`test_audit_logs_to_csv`：

```python
from datetime import datetime
from src.modules.audit_log.model import AuditLog
from src.modules.audit_log.service import audit_logs_to_csv
from src.core.base_model import BaseModel

def test_audit_log_model_registered():
    assert AuditLog.__tablename__ == "audit_logs"
    assert issubclass(AuditLog, BaseModel)
    assert hasattr(AuditLog, "target_id") and hasattr(AuditLog, "user_agent")

def test_audit_logs_to_csv():
    logs = [AuditLog(user_id="user-001", username="admin", action="create", module="agent",
                     target_id="a1", target_name="智能客服", detail="创建", ip_address="10.0.0.1",
                     user_agent="Mozilla", created_at=datetime(2024, 2, 7, 10, 30))]
    csv = audit_logs_to_csv(logs)
    assert csv.splitlines()[0] == "时间,用户,操作,模块,对象,详情,IP地址"
    assert "admin" in csv and "智能客服" in csv
```

- [ ] **Step 2: 运行确认失败 → 实现 `model.py` + 纯函数 → 运行确认通过**

Run: `pytest test/test_audit_log.py::test_audit_log_model_registered -v` → FAIL（模块未建）。实现 `model.py`（字段见 Produces）与 `service.py` 中的 `audit_logs_to_csv`（用 `csv` 标准库或字符串拼接，字段顺序：created_at、username、action、module、target_name、detail、ip_address）。创建 `__init__.py`。再 Run 两个测试 → PASS。

- [ ] **Step 3: 写失败测试（repository 筛选）**

```python
import pytest
from datetime import datetime
from src.modules.audit_log.repository import AuditLogRepository
from src.modules.audit_log.schema import AuditLogFilter
from src.modules.audit_log.model import AuditLog

@pytest.mark.asyncio
async def test_filtered_page_by_action_and_module(db_session):
    repo = AuditLogRepository(db_session)
    await repo.create(AuditLog(user_id="u1", username="admin", action="create", module="agent",
        detail="创建", ip_address="10.0.0.1", created_at=datetime(2024,2,7,10,30)))
    await repo.create(AuditLog(user_id="u2", username="张三", action="login", module="system",
        detail="登录", ip_address="10.0.0.2", created_at=datetime(2024,2,8,9,0)))
    items, total = await repo.filtered_page(0, 20, None, AuditLogFilter(action="login", module="system"))
    assert total == 1 and items[0].username == "张三"
```

- [ ] **Step 4: 运行确认失败 → 实现 `schema.py` + `repository.py` → 运行确认通过**

Run: `pytest test/test_audit_log.py::test_filtered_page_by_action_and_module -v` → FAIL。实现 `schema.py`（`AuditLogFilter`、`AuditLogRead`）与 `repository.py`：`filtered_page`/`filtered_all` 基于 `select(AuditLog)` 依次叠加等值 WHERE（user_id/action/module）与 `created_at >= start_time`/`<= end_time`，`keyword` 对 `username`/`detail` 做 OR 模糊，总数 `func.count()` 子查询，按 `id.asc()`。再 Run → PASS。

- [ ] **Step 5: 写失败测试（service）**

```python
import pytest
from src.core.deps import PageParams
from src.modules.audit_log.service import AuditLogService
from src.modules.audit_log.schema import AuditLogFilter
from src.modules.audit_log.model import AuditLog

@pytest.mark.asyncio
async def test_list_audit_logs_empty_result(db_session):
    svc = AuditLogService(db_session)
    page = await svc.list_logs(PageParams(page=1, page_size=10, keyword=None),
                               AuditLogFilter(action="nonexistent"))
    assert page.total == 0 and page.items == []
```

- [ ] **Step 6: 运行确认失败 → 实现 `service.py` → 运行确认通过**

Run: `pytest test/test_audit_log.py::test_list_audit_logs_empty_result -v` → FAIL。实现 `AuditLogService`：`list_logs` 调 `repo.filtered_page` 并逐条 `AuditLogRead.model_validate`；`export_csv` 调 `repo.filtered_all` 后 `audit_logs_to_csv`。再 Run → PASS。

- [ ] **Step 7: 写失败测试（api 路由）→ 实现 `api.py` + 注册 `main.py` → 运行确认通过**

在 `test/test_audit_log.py` 追加：

```python
from src.modules.audit_log.api import router

def test_audit_log_routes_registered():
    paths = {r.path for r in router.routes}
    assert "/system/audit-logs" in paths
    assert "/system/audit-logs/export" in paths
```

实现 `api.py`：`router = APIRouter(prefix="/system/audit-logs", tags=["系统管理"])`；`GET ""`（`AuditLogFilter` 查询参数 + `PageParams`）→ `ResponseSchema[PageResult[AuditLogRead]]`；`GET "/export"`（`AuditLogFilter`）→ `Response(content=csv, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="audit-logs.csv"'})`。两个路由均加 `Depends(get_current_user_with_permission("system:audit"))`。在 `src/main.py` 注册。Run → PASS；`python -c "from src.main import app"` 确认无错。

- [ ] **Step 8: Commit**

```bash
git add src/modules/audit_log/ test/test_audit_log.py src/main.py
git commit -m "feat: 审计日志子模块实现"
```

---

### Task 4: 告警规则 + 活跃告警子模块

**Files:**
- Create: `src/modules/alert_rule/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py`
- Modify: `src/main.py`
- Test: `test/test_alert_rule.py`

**Interfaces:**
- Consumes: Task 1 `get_current_user_with_permission`；Task 2 `db_session` fixture；`BaseModel`/`BaseRepository`/`PageParams`/`PageResult`/`ResponseSchema`/`BizException`/`get_db`。
- Produces:
  - `class AlertRule(BaseModel)`：`__tablename__ = "alert_rules"`，字段 `name: str(String(100))`、`description: str | None(String(200))`、`condition: dict(JSON)`、`notification: dict | None(JSON)`、`status: str(String(20), default="enabled")`、`created_by: str | None(String(100))`。
  - `class Alert(BaseModel)`：`__tablename__ = "alerts"`，字段 `type: str(String(20))`、`title: str(String(200))`、`message: str(Text)`、`source: str(String(50))`、`severity: str(String(20))`、`status: str(String(20), default="active")`、`count: int(Integer, default=1)`、`first_occurred_at: datetime`、`last_occurred_at: datetime`、`acknowledged_by: str | None(String(100))`、`acknowledged_at: datetime | None`、`resolved_at: datetime | None`。
  - `class AlertCondition(BaseModel)`：`metric: str`、`operator: Literal["gt","lt","eq","gte","lte"]`、`threshold: float`、`duration: int`、`scope: str | None = None`。
  - `class AlertNotification(BaseModel)`：`channels: list[Literal["email","webhook","sms"]]`、`recipients: list[str]`。
  - `class AlertRuleCreate(BaseModel)`：`name: str`、`description: str|None=None`、`condition: AlertCondition`、`notification: AlertNotification|None=None`、`status: Literal["enabled","disabled"]="enabled"`。
  - `class AlertRuleUpdate(BaseModel)`：同名字段全 `|None=None`（`condition`/`notification` 亦 `|None`）。
  - `class AlertRuleRead(BaseModel)`（`from_attributes`）：`id:int`、`name:str`、`description:str|None`、`condition:dict`、`notification:dict|None`、`status:str`、`created_by:str|None`、`created_at:datetime`、`updated_at:datetime`。
  - `class AlertRead(BaseModel)`（`from_attributes`）：`id:int`、`type:str`、`title:str`、`message:str`、`source:str`、`severity:str`、`status:str`、`count:int`、`first_occurred_at:datetime`、`last_occurred_at:datetime`、`acknowledged_by:str|None`、`acknowledged_at:datetime|None`、`resolved_at:datetime|None`。
  - `class AlertRuleRepository(BaseRepository[AlertRule])`：`SEARCH_FIELDS = ["name"]`；`async def search_page(self, offset: int, limit: int, keyword: str | None) -> tuple[list[AlertRule], int]`。
  - `class AlertRepository(BaseRepository[Alert])`：`async def list_by_status(self, status: str | None = None, severity: str | None = None) -> list[Alert]`（`id.desc()`）。
  - `class AlertService`：`__init__(self, db: AsyncSession)`；`list_rules(params: PageParams) -> PageResult[AlertRuleRead]`；`create_rule(data: AlertRuleCreate, current_user: str | None) -> AlertRuleRead`；`update_rule(rule_id: int, data: AlertRuleUpdate) -> AlertRuleRead`（不存在抛 `47002`）；`delete_rule(rule_id: int) -> None`（不存在抛 `47002`）；`list_alerts(status: str | None = None, severity: str | None = None) -> list[AlertRead]`；`acknowledge_alert(alert_id: int, username: str) -> AlertRead`（不存在抛 `47003`，非 `active` 抛 `47004`）；`resolve_alert(alert_id: int) -> AlertRead`（不存在抛 `47003`，已 `resolved` 抛 `47005`）。
  - `router = APIRouter(prefix="/system/alerts", tags=["系统管理"])` 与 `def get_alert_service(db: AsyncSession = Depends(get_db)) -> AlertService`。

- [ ] **Step 1: 写失败测试（模型）**

在 `test/test_alert_rule.py` 写 `test_alert_models_registered`：

```python
from src.modules.alert_rule.model import AlertRule, Alert
from src.core.base_model import BaseModel

def test_alert_models_registered():
    assert AlertRule.__tablename__ == "alert_rules"
    assert Alert.__tablename__ == "alerts"
    assert issubclass(AlertRule, BaseModel) and issubclass(Alert, BaseModel)
    assert hasattr(AlertRule, "condition") and hasattr(AlertRule, "notification")
    assert hasattr(Alert, "first_occurred_at") and hasattr(Alert, "acknowledged_by")
```

- [ ] **Step 2: 运行确认失败 → 实现 `model.py` → 运行确认通过**

Run: `pytest test/test_alert_rule.py::test_alert_models_registered -v` → FAIL（模块未建）。实现 `model.py`（`condition`/`notification` 用 `mapped_column(JSON)`，`condition` 非空 `nullable=False`，`notification` 可空）。创建 `__init__.py`。再 Run → PASS。

- [ ] **Step 3: 写失败测试（schema）→ 实现 `schema.py` → 运行确认通过**

在 `test/test_alert_rule.py` 追加：

```python
import pytest
from pydantic import ValidationError
from src.modules.alert_rule.schema import AlertRuleCreate

def test_alert_rule_condition_operator_literal():
    ok = AlertRuleCreate(name="错误率告警",
                         condition={"metric": "error_rate", "operator": "gt", "threshold": 10, "duration": 5})
    assert ok.condition.operator == "gt"
    with pytest.raises(ValidationError):
        AlertRuleCreate(name="bad", condition={"metric": "x", "operator": ">=", "threshold": 1, "duration": 1})
```

Run → FAIL（schema 未建）。实现 `schema.py`（按 Produces 九个模型；`AlertRuleRead`/`AlertRead` 加 `from_attributes`；`condition` 用 `AlertCondition` 子模型、`notification` 用 `AlertNotification`）。再 Run → PASS。

- [ ] **Step 4: 写失败测试（service，规则 CRUD + 告警确认/解决）**

```python
import pytest
from datetime import datetime
from src.core.exceptions import BizException
from src.core.deps import PageParams
from src.modules.alert_rule.service import AlertService
from src.modules.alert_rule.schema import AlertRuleCreate
from src.modules.alert_rule.model import Alert

def _make_alert(status="active"):
    return Alert(type="error", title="API失败率过高", message="失败率15%", source="monitoring",
                 severity="high", status=status, count=1,
                 first_occurred_at=datetime(2024,2,7,10,0), last_occurred_at=datetime(2024,2,7,10,0))

@pytest.mark.asyncio
async def test_create_and_list_rules(db_session):
    svc = AlertService(db_session)
    created = await svc.create_rule(AlertRuleCreate(
        name="错误率告警",
        condition={"metric": "error_rate", "operator": "gt", "threshold": 10, "duration": 5},
        notification={"channels": ["email"], "recipients": ["admin@cg.ai"]}), current_user="admin")
    assert created.condition["operator"] == "gt"
    page = await svc.list_rules(PageParams(page=1, page_size=10, keyword=None))
    assert page.total == 1 and page.items[0].name == "错误率告警"

@pytest.mark.asyncio
async def test_acknowledge_and_resolve_alert(db_session):
    svc = AlertService(db_session)
    await svc.alert_repo.create(_make_alert("active"))
    ack = await svc.acknowledge_alert(1, "admin")
    assert ack.status == "acknowledged" and ack.acknowledged_by == "admin" and ack.acknowledged_at is not None
    res = await svc.resolve_alert(1)
    assert res.status == "resolved" and res.resolved_at is not None

@pytest.mark.asyncio
async def test_acknowledge_missing_alert(db_session):
    svc = AlertService(db_session)
    with pytest.raises(BizException) as e:
        await svc.acknowledge_alert(999, "admin")
    assert e.value.code == 47003

@pytest.mark.asyncio
async def test_acknowledge_resolved_alert_fails(db_session):
    svc = AlertService(db_session)
    await svc.alert_repo.create(_make_alert("resolved"))
    with pytest.raises(BizException) as e:
        await svc.acknowledge_alert(1, "admin")
    assert e.value.code == 47004

@pytest.mark.asyncio
async def test_resolve_already_resolved_fails(db_session):
    svc = AlertService(db_session)
    await svc.alert_repo.create(_make_alert("resolved"))
    with pytest.raises(BizException) as e:
        await svc.resolve_alert(1)
    assert e.value.code == 47005
```

- [ ] **Step 5: 运行确认失败 → 实现 `repository.py` + `service.py` → 运行确认通过**

Run: `pytest test/test_alert_rule.py::test_create_and_list_rules -v` → FAIL（service 未建）。实现 `repository.py`（两个 repo，`search_page`/`list_by_status` 见 Produces）与 `service.py`：`AlertService.__init__` 建 `self.rule_repo = AlertRuleRepository(db)`、`self.alert_repo = AlertRepository(db)`；`create_rule` 将 `condition`/`notification` 用 `.model_dump()` 存 JSON；`acknowledge_alert` 查 `alert_repo.get_by_id` 不存在抛 `47003`，`status != "active"` 抛 `47004`，否则置 `acknowledged_by=username`、`acknowledged_at=datetime.now()`、`status="acknowledged"` 并 `update`；`resolve_alert` 不存在抛 `47003`，`status == "resolved"` 抛 `47005`，否则置 `resolved_at=datetime.now()`、`status="resolved"` 并 `update`。再 Run 5 个测试 → PASS。

- [ ] **Step 6: 写失败测试（api 路由）→ 实现 `api.py` + 注册 `main.py` → 运行确认通过**

在 `test/test_alert_rule.py` 追加：

```python
from src.modules.alert_rule.api import router

def test_alert_routes_registered():
    paths = {r.path for r in router.routes}
    assert "/system/alerts/rules" in paths
    assert "/system/alerts/rules/{rule_id}" in paths
    assert "/system/alerts/active" in paths
    assert "/system/alerts/{alert_id}/acknowledge" in paths
    assert "/system/alerts/{alert_id}/resolve" in paths
```

实现 `api.py`：`router = APIRouter(prefix="/system/alerts", tags=["系统管理"])`；`GET "/rules"`（`PageParams`）→ `ResponseSchema[PageResult[AlertRuleRead]]`；`POST "/rules"` → `ResponseSchema[AlertRuleRead]`；`PUT "/rules/{rule_id}"` → `ResponseSchema[AlertRuleRead]`；`DELETE "/rules/{rule_id}"` → `ResponseSchema`；`GET "/active"`（`status: str|None`、`severity: str|None` 查询参数）→ `ResponseSchema[list[AlertRead]]`；`POST "/{alert_id}/acknowledge"`（`current_user: User = Depends(get_current_user_with_permission("system:alerts"))` 并传 `current_user.username`）→ `ResponseSchema[AlertRead]`；`POST "/{alert_id}/resolve"` → `ResponseSchema[AlertRead]`。所有路由均挂 `system:alerts` 权限。在 `src/main.py` 注册。Run → PASS；`python -c "from src.main import app"` 确认无错。

- [ ] **Step 7: Commit**

```bash
git add src/modules/alert_rule/ test/test_alert_rule.py src/main.py
git commit -m "feat: 告警规则与活跃告警子模块实现"
```

---

### Task 5: 系统配置子模块

**Files:**
- Create: `src/modules/system_settings/__init__.py`、`model.py`、`schema.py`、`repository.py`、`service.py`、`api.py`
- Modify: `src/main.py`
- Test: `test/test_system_settings.py`

**Interfaces:**
- Consumes: Task 1 `get_current_user_with_permission`；Task 2 `db_session` fixture；`BaseModel`/`BaseRepository`/`ResponseSchema`/`get_db`。
- Produces:
  - `class SystemSettings(BaseModel)`：`__tablename__ = "system_settings"`，字段 `system_name: str(String(100), default="辰光Agent平台")`、`system_description: str | None(Text)`、`default_language: str(String(20), default="zh-CN")`、`default_model: str(String(100), default="GPT-4")`、`default_temperature: float(Float, default=0.7)`、`default_max_tokens: int(Integer, default=4096)`、`smtp_server: str | None(String(200))`、`smtp_port: int(Integer, default=587)`、`sender_email: str | None(String(100))`。
  - `class SystemSettingsUpdate(BaseModel)`：与上同名字段（`system_name: str` 必填，`system_description`/`smtp_server`/`sender_email` 可空，其余必填）。
  - `class SystemSettingsRead(BaseModel)`（`from_attributes`）：与 `SystemSettings` ORM 同名的 9 个字段（不含 `id`/`created_at`/`updated_at`，与前端 `SystemSettings` 类型一致）。
  - `class SystemSettingsRepository(BaseRepository[SystemSettings])`：`async def get_first(self) -> SystemSettings | None`。
  - `class SystemSettingsService`：`__init__(self, db: AsyncSession)`；`async def get_settings(self) -> SystemSettingsRead`（无行时用默认值建一行）；`async def update_settings(self, data: SystemSettingsUpdate) -> SystemSettingsRead`（无行时建行，有行时逐字段整体覆盖）。
  - `router = APIRouter(prefix="/system/settings", tags=["系统管理"])` 与 `def get_system_settings_service(db: AsyncSession = Depends(get_db)) -> SystemSettingsService`。

- [ ] **Step 1: 写失败测试（模型）**

在 `test/test_system_settings.py` 写 `test_system_settings_model_registered`：

```python
from src.modules.system_settings.model import SystemSettings
from src.core.base_model import BaseModel

def test_system_settings_model_registered():
    assert SystemSettings.__tablename__ == "system_settings"
    assert issubclass(SystemSettings, BaseModel)
    assert hasattr(SystemSettings, "default_temperature") and hasattr(SystemSettings, "smtp_port")
```

- [ ] **Step 2: 运行确认失败 → 实现 `model.py` → 运行确认通过**

Run: `pytest test/test_system_settings.py::test_system_settings_model_registered -v` → FAIL（模块未建）。实现 `model.py`（`default_temperature` 用 `mapped_column(Float, default=0.7)`）。创建 `__init__.py`。再 Run → PASS。

- [ ] **Step 3: 写失败测试（schema + service）**

```python
import pytest
from src.modules.system_settings.schema import SystemSettingsUpdate
from src.modules.system_settings.service import SystemSettingsService

@pytest.mark.asyncio
async def test_get_settings_creates_defaults(db_session):
    svc = SystemSettingsService(db_session)
    read = await svc.get_settings()
    assert read.system_name == "辰光Agent平台"
    assert read.default_temperature == 0.7
    assert read.smtp_port == 587

@pytest.mark.asyncio
async def test_update_settings_overwrites(db_session):
    svc = SystemSettingsService(db_session)
    await svc.update_settings(SystemSettingsUpdate(
        system_name="新平台", default_language="en-US", default_model="GPT-4o",
        default_temperature=0.9, default_max_tokens=8192, smtp_port=465))
    read = await svc.get_settings()
    assert read.system_name == "新平台"
    assert read.default_temperature == 0.9
    assert read.default_max_tokens == 8192
```

- [ ] **Step 4: 运行确认失败 → 实现 `schema.py` + `repository.py` + `service.py` → 运行确认通过**

Run: `pytest test/test_system_settings.py::test_get_settings_creates_defaults -v` → FAIL。实现 `schema.py`（`SystemSettingsUpdate`/`SystemSettingsRead`）与 `repository.py`（`get_first`：`select(SystemSettings).limit(1)`）与 `service.py`：`get_settings` 取 `get_first()`，无行则 `create(SystemSettings())` 落默认值；`update_settings` 取 `get_first()`，无行则 `create(SystemSettings(**data.model_dump()))`，有行则逐字段赋值后 `update`。再 Run 两个测试 → PASS。

- [ ] **Step 5: 写失败测试（api 路由）→ 实现 `api.py` + 注册 `main.py` → 运行确认通过**

在 `test/test_system_settings.py` 追加：

```python
from src.modules.system_settings.api import router

def test_system_settings_routes_registered():
    assert {r.path for r in router.routes} == {"/system/settings"}
```

实现 `api.py`：`router = APIRouter(prefix="/system/settings", tags=["系统管理"])`；`GET ""` → `ResponseSchema[SystemSettingsRead]`；`PUT ""` → `ResponseSchema[SystemSettingsRead]`。两路由均加 `Depends(get_current_user_with_permission("system:settings"))`。在 `src/main.py` 注册。Run → PASS；`python -c "from src.main import app"` 确认无错。

- [ ] **Step 6: Commit**

```bash
git add src/modules/system_settings/ test/test_system_settings.py src/main.py
git commit -m "feat: 系统配置子模块实现"
```

---

### Task 6: Alembic 迁移 + 应用装配校验

**Files:**
- Modify: `alembic/env.py:33-41`（追加 4 个 model 导入）
- Create: `alembic/versions/<hash>_系统管理扩展5表.py`（autogenerate 生成）
- Modify: `src/main.py`（确认 4 个 router 均已注册）

**Interfaces:**
- Consumes: Task 2-5 的 `ApiKey`/`AuditLog`/`AlertRule`/`Alert`/`SystemSettings` ORM（均已 import 进 `src.main`）。
- Produces: 一张迁移文件，含 5 张表 `api_keys`、`audit_logs`、`alert_rules`、`alerts`、`system_settings`。

- [ ] **Step 1: 在 `alembic/env.py` 注册新模型**

在模块导入区（`import src.modules.agent.model` 之后）追加：

```python
import src.modules.api_key.model
import src.modules.audit_log.model
import src.modules.alert_rule.model
import src.modules.system_settings.model
```

- [ ] **Step 2: 生成迁移**

Run: `alembic revision --autogenerate -m "系统管理扩展5表"`
Expected: 生成 `alembic/versions/<hash>_系统管理扩展5表.py`，`upgrade()` 含 5 个 `op.create_table`（`api_keys` 带 `UniqueConstraint('key')`；`alerts` 含 `first_occurred_at`/`last_occurred_at` 非空 datetime）。

- [ ] **Step 3: 应用迁移确认**

Run: `alembic upgrade head`
Expected: 无报错，5 张表创建成功。

- [ ] **Step 4: 全量测试 + 装配校验**

Run: `pytest -q`
Expected: 全部测试通过（含既有 `test/test_jwt.py` 等与新增 `test/test_api_key.py`、`test/test_audit_log.py`、`test/test_alert_rule.py`、`test/test_system_settings.py`、`test/test_permission_dep.py`）。

Run: `python -c "from src.main import app; paths={r.path for r in app.routes}; assert {'/api/v1/system/api-keys','/api/v1/system/audit-logs','/api/v1/system/alerts/rules','/api/v1/system/settings'} <= paths; print('OK')"`
Expected: 打印 `OK`。

- [ ] **Step 5: Commit**

```bash
git add alembic/env.py alembic/versions/<hash>_系统管理扩展5表.py src/main.py
git commit -m "feat: 系统管理扩展数据库迁移"
```
