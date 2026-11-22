# 工作台（Dashboard）后端模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从 0 新建后端模块 `src/modules/dashboard/`，对 Agent / 对话 / 告警 / 知识库做聚合查询，提供工作台首页 5 个只读数据接口。

**Architecture:** 遵循仓库 5 层架构（model → schema → repository → service → api），但工作台没有独立业务表：repository 层直接聚合查询外部表。其中 `agents`、`knowledge_bases` 已存在，直接导入其 ORM 模型；`conversations`、`alerts` 是外部依赖（由后续「对话日志」和「系统管理扩展」模块拥有），本模块用只读 ORM 模型声明读取契约，并在表缺失时降级为 0 / 空列表。API 返回字段名与前端 `types/dashboard.ts` 完全一致（camelCase）。

**Tech Stack:** Python 3.13、FastAPI（async）、SQLAlchemy 2.0（`Mapped`/`mapped_column`）、Pydantic v2、pytest + pytest-asyncio、aiosqlite（本地/测试库）。

**Spec:** `app/docs/01-工作台.md`（页面与数据大盘设计）；前端类型权威来源 `app/src/services/types/dashboard.ts`；前端调用路径 `app/src/services/api/dashboard.ts`。项目级约束见 `docs/PROJECT_SPEC.md` 与 `docs/spec/PROJECT_SPEC_V2.md`。

## Global Constraints

- 后端 Python 3.13 + FastAPI 异步；ORM 继承 `BaseModel`（自带 `id`/`created_at`/`updated_at`），字段用 `Mapped`/`mapped_column`，JSON 用 `mapped_column(JSON)`。
- 路由统一 `/api/v1` 前缀，在 `src/main.py` 用 `app.include_router(router, prefix="/api/v1")` 注册。
- 响应统一 `ResponseSchema(code=200, message="success", data=...)`；工作台 5 个接口均返回单对象或 `list`，不用 `PageResult`。
- 业务异常用 `BizException(code, message)`，全局处理器返回 HTTP 200 + `{"code":..., "message":..., "data":null}`（`core/exceptions.py` 已实现）。
- 认证用 `Depends(get_current_user)`（JWT 校验，`core/deps.py` 已实现）。工作台是登录后首页，V2 权限码清单中**没有** `dashboard:*`，因此只要求登录、不加 `get_current_user_with_permission`。
- 前端字段名/类型以 `app/src/services/types/dashboard.ts` 为权威，全部 **camelCase**：`todayCalls`、`tokenUsage`、`agentId`、`successRate`、`avgLatency`、`activeAgentsTrend` 等。后端 JSON 键必须一一对应（与 agent 模块的 snake_case 不同，本模块 schema 直接使用 camelCase 字段名）。
- 测试 pytest + pytest-asyncio，测试文件放 `/test/`，命令 `pytest test/test_dashboard.py::test_name -v`。
- 提交消息中文摘要格式（如 `feat: 工作台 schema 定义`）。
- 数据库：本地开发/测试用 SQLite（aiosqlite，`src/core/config.py` 的 `DATABASE_URL` 返回 `sqlite+aiosqlite:///./chenguang.db`），生产用 MySQL。

## Review Focus

以下 5 类输入/边界最可能让使用者踩坑，各配一条测试并归属到对应 Task：

1. **空库 / 无对话数据**：今日调用数为 0 时，趋势环比（较昨日）不能因分母为 0 而抛异常，应返回 0.0；趋势图仍应返回 7 个点（全 0）。→ Task 3 测试 `test_stats_zero_division`、`test_trends_seven_days_fill`。
2. **依赖表尚未建（conversations / alerts 模块未上线）**：查询缺失的表会抛 `OperationalError`，repository 必须捕获并降级返回 0 / 空列表，而不是让整个工作台 500。→ Task 2 测试 `test_repo_degradation_missing_tables`。
3. **日期边界（“今日/昨日”与 7 天窗口）**：恰好落在本地午夜边界的会话要归到正确的一天；趋势必须恰好 7 天、升序、以今天结尾。→ Task 3 测试 `test_trends_seven_days_fill`。
4. **成功率语义**：`successRate` 必须是 0–100 的百分比（不是 0–1），且 `avgLatency` 单位是秒、保留 1 位小数；`agentId` 是字符串（后端 id 是 int）。→ Task 3 测试 `test_top_agents_string_id_and_percent`。
5. **前端字段名契约（camelCase）**：序列化后 JSON 键必须与前端 `types/dashboard.ts` 完全一致（如 `todayCalls` 而非 `today_calls`），否则前端拿到 `undefined`。→ Task 1 测试 `test_dashboard_stats_camelcase_serialization`。

---

## File Structure

- Create: `src/modules/dashboard/__init__.py` — 模块空文件。
- Create: `src/modules/dashboard/schema.py` — 5 个只读 Pydantic 模型（`DashboardStats`/`TrendData`/`AgentRanking`/`Alert`/`ResourceUsage`），camelCase 字段，镜像前端类型。
- Create: `src/modules/dashboard/model.py` — 只读 ORM 契约模型 `Conversation`、`AlertRecord`（挂独立 `DashboardBase`，避免与主 `Base.metadata` 冲突）；不新增迁移、不建表。
- Create: `src/modules/dashboard/repository.py` — `DashboardRepository`：对 `agents`/`knowledge_bases`/`conversations`/`alerts` 的聚合查询 + 缺失表降级。
- Create: `src/modules/dashboard/service.py` — `DashboardService`：把聚合结果组装为 schema，计算环比、补全 7 天、格式化日期/时间、静态资源值。
- Create: `src/modules/dashboard/api.py` — `APIRouter(prefix="/dashboard")`，5 个 GET 路由。
- Modify: `src/main.py` — 导入并注册 `dashboard_router`。
- Test: `test/test_dashboard.py` — schema/repository/service/api 四层测试，含 SQLite 内存库 fixture。

---

### Task 1: schema.py —— 5 个只读 Pydantic 模型

**Files:**
- Create: `src/modules/dashboard/__init__.py`
- Create: `src/modules/dashboard/schema.py`
- Test: `test/test_dashboard.py`

**Interfaces:**
- Consumes: 无（本模块第一个任务）。
- Produces: 5 个 Pydantic 模型，字段名/类型/枚举如下（后续 Task 3/4 依赖）：
  - `DashboardStats`: `todayCalls: int`, `todayCallsTrend: float`, `tokenUsage: int`, `tokenUsageTrend: float`, `cost: float`, `costTrend: float`, `activeAgents: int`, `totalAgents: int`, `activeAgentsTrend: int`
  - `TrendData`: `date: str`, `calls: int`, `tokens: int`
  - `AgentRanking`: `agentId: str`, `agentName: str`, `calls: int`, `successRate: float`, `avgLatency: float`
  - `Alert`: `id: str`, `level: Literal["info","warning","error","critical"]`, `message: str`, `time: str`, `status: Literal["active","acknowledged","resolved"]`
  - `ResourceUsage`: `name: str`, `used: float`, `total: float`, `percentage: float`, `unit: str`

- [ ] **Step 1: 写失败测试**

在 `test/test_dashboard.py` 中写 3 个测试（`from src.modules.dashboard.schema import DashboardStats, TrendData, AgentRanking, Alert, ResourceUsage`）：

```python
from pydantic import ValidationError

def test_dashboard_stats_camelcase_serialization():
    s = DashboardStats(todayCalls=10, todayCallsTrend=1.5, tokenUsage=100,
                       tokenUsageTrend=2.5, cost=1.0, costTrend=3.5,
                       activeAgents=2, totalAgents=5, activeAgentsTrend=0)
    assert set(s.model_dump().keys()) == {
        "todayCalls", "todayCallsTrend", "tokenUsage", "tokenUsageTrend",
        "cost", "costTrend", "activeAgents", "totalAgents", "activeAgentsTrend"}

def test_alert_level_and_status_enums():
    a = Alert(id="1", level="critical", message="x", time="14:32", status="active")
    assert a.level == "critical"
    try:
        Alert(id="2", level="bogus", message="x", time="14:32", status="active")
    except ValidationError:
        pass
    else:
        raise AssertionError("level 非法值应抛 ValidationError")

def test_resource_usage_field_types():
    r = ResourceUsage(name="存储空间", used=6.2, total=10, percentage=62.0, unit="GB")
    assert r.used == 6.2 and r.percentage == 62.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_dashboard.py -v`
Expected: FAIL，报 `ModuleNotFoundError: No module named 'src.modules.dashboard.schema'`。

- [ ] **Step 3: 实现 `schema.py` 中的 5 个模型**

创建 `src/modules/dashboard/schema.py` 与空的 `__init__.py`。每个模型用上述 Produces 里的精确字段名与类型；`Alert` 的 `level`/`status` 用 `typing.Literal`，`ResourceUsage` 的数值字段用 `float`。字段名必须保持 camelCase（这是与前端契约，不要用 snake_case）。不需要 `from_attributes`（这些是服务层手工构造的只读对象）。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_dashboard.py -v`
Expected: PASS（3 passed）。

- [ ] **Step 5: Commit**

```bash
git add src/modules/dashboard/__init__.py src/modules/dashboard/schema.py test/test_dashboard.py
git commit -m "feat: 工作台 schema 定义"
```

---

### Task 2: model.py + repository.py —— 只读契约模型与聚合查询

**Files:**
- Create: `src/modules/dashboard/model.py`
- Create: `src/modules/dashboard/repository.py`
- Test: `test/test_dashboard.py`（追加测试 + 内存库 fixture）

**Interfaces:**
- Consumes:
  - 已存在 ORM：`Agent`（`src.modules.agent.model`，含 `id`、`name`、`status`）；`KnowledgeBase`（`src.modules.knowledge.model`，含 `id`）。
  - 外部依赖表读取契约（本模块只读，不建表、不加迁移；由「对话日志」「系统管理扩展」模块负责建表）：
    - 表 `conversations`：`id`(int PK)、`agent_id`(int, FK agents.id)、`status`(str: active/completed/error)、`turn_count`(int)、`total_tokens`(int)、`total_cost`(Numeric(10,4))、`total_duration`(float, 秒)、`created_at`(datetime)。
    - 表 `alerts`：`id`(int PK)、`level`(str: info/warning/error/critical)、`message`(str)、`status`(str: active/acknowledged/resolved)、`created_at`(datetime)。
- Produces: `DashboardRepository`，方法签名（返回值供 Task 3 使用）：
  - `async count_active_agents(self) -> int` —— `Agent.status == "active"` 计数。
  - `async count_total_agents(self) -> int` —— `Agent` 总数。
  - `async sum_tokens_between(self, start: datetime, end: datetime) -> int` —— `conversations.total_tokens` 求和（`created_at` 落在 `[start, end)`）；表缺失降级返回 0。
  - `async sum_cost_between(self, start: datetime, end: datetime) -> float` —— 同上，`total_cost` 求和；降级返回 0.0。
  - `async count_conversations_between(self, start: datetime, end: datetime) -> int` —— 同上，计数；降级返回 0。
  - `async daily_calls_tokens(self, days: int) -> list[tuple[date, int, int]]` —— 最近 `days` 天按 `created_at` 日期分组，返回 `(日期, 调用数, token 数)` 升序，仅含**有数据**的天；降级返回 `[]`。
  - `async top_agents(self, limit: int) -> list[dict]` —— 按 `agent_id` 分组、JOIN `agents.name`，返回 `[{"agent_id": int, "agent_name": str, "calls": int, "success_rate": float, "avg_latency": float}]`，按 `calls` 降序取前 `limit` 条；降级返回 `[]`。`success_rate` = 100 * 非 error 会话数 / 总会话数；`avg_latency` = `total_duration` 平均值（秒）。
  - `async recent_alerts(self, limit: int) -> list[AlertRecord]` —— 按 `created_at` 降序取前 `limit` 条；降级返回 `[]`。
  - `async count_knowledge_bases(self) -> int` —— `KnowledgeBase` 计数。

- [ ] **Step 1: 写失败测试 + 内存库 fixture**

在 `test/test_dashboard.py` 顶部加 fixture（注意：内存 SQLite + async 必须用 `StaticPool` 共享同一连接）：

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.core.base_model import Base
from src.modules.agent.model import Agent
from src.modules.knowledge.model import KnowledgeBase
from src.modules.dashboard.model import DashboardBase, Conversation, AlertRecord

@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # 先建主 Base 的表（agents / knowledge_bases），再建 DashboardBase 的表（conversations / alerts）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(DashboardBase.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()
```

再写 repository 测试（`from src.modules.dashboard.repository import DashboardRepository`），至少覆盖：seed 5 个 Agent（3 active + 2 inactive）断言 `count_active_agents()==3`、`count_total_agents()==5`；seed 跨两天的 conversations 断言 `count/sum` 与 `daily_calls_tokens` 的日期升序与数量；seed 2 个 agent 的会话（含 error 状态）断言 `top_agents` 的 calls/success_rate/avg_latency。

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_dashboard.py -v`
Expected: FAIL，报 `ModuleNotFoundError: No module named 'src.modules.dashboard.model'`（或 `repository`）。

- [ ] **Step 3: 实现 `model.py` 与 `repository.py`**

`model.py`：定义独立 `class DashboardBase(DeclarativeBase): pass`，在其上定义只读 `Conversation`（`__tablename__ = "conversations"`）与 `AlertRecord`（`__tablename__ = "alerts"`），字段用 `Mapped`/`mapped_column`，列名/类型严格按 Consumes 契约（`total_cost` 用 `Numeric(10, 4)`，`total_duration` 用 `Float`，均含 `created_at: Mapped[datetime]`）。**不要**让它们继承主 `Base`/`BaseModel`，避免与未来模块的建表冲突。文件顶部用注释声明“这些是只读契约模型，表由对话日志 / 系统管理扩展模块创建”。

`repository.py`：`DashboardRepository(db: AsyncSession)`，导入 `Agent`、`KnowledgeBase` 与 `Conversation`、`AlertRecord`。对 conversations / alerts 的 6 个方法，用 `try/except` 捕获 SQLAlchemy `OperationalError`/`ProgrammingError`（表不存在）并返回对应降级值（0 / 0.0 / []）。`daily_calls_tokens` 用 `func.date(Conversation.created_at)` 分组并把字符串转 `datetime.date`；`top_agents` 用 `func.sum(case(...))` 算非 error 数、`func.avg(Conversation.total_duration)` 算平均延迟。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_dashboard.py -v`
Expected: PASS（Task 1 的 3 个 + Task 2 新增全部通过）。

- [ ] **Step 5: Commit**

```bash
git add src/modules/dashboard/model.py src/modules/dashboard/repository.py test/test_dashboard.py
git commit -m "feat: 工作台聚合查询仓库层"
```

---

### Task 3: service.py —— 聚合业务逻辑与降级/环比/格式化

**Files:**
- Create: `src/modules/dashboard/service.py`
- Test: `test/test_dashboard.py`（追加 service 测试）

**Interfaces:**
- Consumes: Task 1 的 5 个 schema；Task 2 的 `DashboardRepository` 全部方法。
- Produces: `DashboardService`，方法签名（Task 4 依赖）：
  - `async get_stats(self) -> DashboardStats`
  - `async get_trends(self) -> list[TrendData]`
  - `async get_top_agents(self) -> list[AgentRanking]`
  - `async get_recent_alerts(self) -> list[Alert]`
  - `async get_resource_usage(self) -> list[ResourceUsage]`
  - 类常量（静态/配置值，来自设计文档「资源用量」表）：`TOKEN_QUOTA_TOTAL = 1_000_000`、`STORAGE_USED_GB = 6.2`、`STORAGE_TOTAL_GB = 10.0`、`CONCURRENCY_USED = 40`、`CONCURRENCY_TOTAL = 100`、`KNOWLEDGE_BASE_TOTAL = 20`。

行为约定（必须实现，测试会断言）：
- `get_stats`：`todayCalls`/`tokenUsage`/`cost` = 今日 `[今日0点, 明日0点)` 的 count/sum_tokens/sum_cost；三个百分比环比 = `(今日-昨日)/昨日*100` 四舍五入 1 位小数，昨日为 0 时返回 `0.0`；`activeAgents`/`totalAgents` = repo 计数；`activeAgentsTrend = 0`（无历史活跃快照数据源，设计为恒 0，代码注释说明）。
- `get_trends`：调用 `daily_calls_tokens(7)` 后，补全最近 7 个自然日（`今天-6` 到 `今天`，缺失日 `calls=0, tokens=0`），升序，`date` 格式化为 `%m-%d`（如 `02-01`）。
- `get_top_agents`：`limit=5`；`agentId = str(agent_id)`、`agentName` 原样、`calls` 原样、`successRate`/`avgLatency` 四舍五入 1 位小数。
- `get_recent_alerts`：`limit=5`；`id = str(record.id)`、`level`/`message`/`status` 原样、`time = created_at.strftime("%H:%M")`。
- `get_resource_usage`：返回 4 条（名称固定为中文）：
  1. `name="Token月度配额"`：`used = float(本月 sum_tokens_between(本月1号0点, now))`，`total = TOKEN_QUOTA_TOTAL`，`unit="tokens"`。
  2. `name="存储空间"`：`used = STORAGE_USED_GB`，`total = STORAGE_TOTAL_GB`，`unit="GB"`（静态值）。
  3. `name="并发连接数"`：`used = CONCURRENCY_USED`，`total = CONCURRENCY_TOTAL`，`unit="个"`（静态值）。
  4. `name="知识库数量"`：`used = float(count_knowledge_bases())`，`total = KNOWLEDGE_BASE_TOTAL`，`unit="个"`。
  - 每条 `percentage = round(used/total*100, 1)`；`total == 0` 时 `percentage = 0.0`。

- [ ] **Step 1: 写失败测试**

追加 service 测试（`from src.modules.dashboard.service import DashboardService`，用 `db_session` fixture seed 数据）。关键断言：

```python
# 今日 10 条、昨日 5 条 → 环比 +100%
# 昨日 0 条 → todayCallsTrend == 0.0（不抛异常）
# 只在 7 天中的 2 天有数据 → get_trends() 长度 == 7、升序、最后一天 == 今天、缺失日为 0
# top_agents 的 agentId 是 str、successRate 在 [0,100]、avgLatency 1 位小数
# activeAgentsTrend == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_dashboard.py -v`
Expected: FAIL，报 `ModuleNotFoundError: No module named 'src.modules.dashboard.service'`。

- [ ] **Step 3: 实现 `DashboardService`**

创建 `src/modules/dashboard/service.py`：`DashboardService.__init__(self, db: AsyncSession)` 持有 `self.repo = DashboardRepository(db)`；按上面 Produces 与行为约定实现 5 个方法。日期边界用 `datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)` 计算今日/昨日/本月起点。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_dashboard.py -v`
Expected: PASS（Task 1/2/3 全部通过）。

- [ ] **Step 5: Commit**

```bash
git add src/modules/dashboard/service.py test/test_dashboard.py
git commit -m "feat: 工作台聚合服务层"
```

---

### Task 4: api.py + main.py 注册 —— 5 个 GET 路由

**Files:**
- Create: `src/modules/dashboard/api.py`
- Modify: `src/main.py`（import + `app.include_router`）
- Test: `test/test_dashboard.py`（追加 API 测试）

**Interfaces:**
- Consumes: Task 3 的 `DashboardService`；`get_db`（`src.infra.database`）、`get_current_user`（`src.core.deps`）、`ResponseSchema`（`src.core.base_schema`）。
- Produces: `router = APIRouter(prefix="/dashboard", tags=["工作台"])`，5 个路由（与前端 `api/dashboard.ts` 路径一致，全走 `Depends(get_current_user)`）：
  - `GET /dashboard/stats` → `ResponseSchema[DashboardStats]`
  - `GET /dashboard/trends` → `ResponseSchema[list[TrendData]]`
  - `GET /dashboard/top-agents` → `ResponseSchema[list[AgentRanking]]`
  - `GET /dashboard/recent-alerts` → `ResponseSchema[list[Alert]]`
  - `GET /dashboard/resource-usage` → `ResponseSchema[list[ResourceUsage]]`
  - 服务工厂：`def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService`。

- [ ] **Step 1: 写失败测试**

追加 API 测试，用 FastAPI 依赖覆盖（`from src.main import app`、`from src.core.deps import get_current_user`、`from src.infra.database import get_db`），用 `httpx.AsyncClient`（`transport=httpx.ASGITransport(app=app)`）+ `app.dependency_overrides` 把 `get_current_user` 覆盖为返回假用户（`SimpleNamespace(id=1, username="admin", is_active=True)`）、`get_db` 覆盖为返回 `db_session`。断言 `GET /api/v1/dashboard/stats` 返回 200 且 `resp.json()["data"]` 含 `todayCalls` 键；`GET /api/v1/dashboard/trends` 的 `data` 是长度 7 的列表。

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_dashboard.py -v`
Expected: FAIL，报 `ModuleNotFoundError: No module named 'src.modules.dashboard.api'`（或 main 未注册该路由 → 404）。

- [ ] **Step 3: 实现 `api.py` 并注册到 `main.py`**

创建 `src/modules/dashboard/api.py`，按 Produces 定义 5 个 `@router.get(...)` 与 `get_dashboard_service`；每个端点 `svc: DashboardService = Depends(get_dashboard_service)`，并在参数中加 `current_user=Depends(get_current_user)`（认证、不做权限码校验）。在 `src/main.py` 顶部 `from src.modules.dashboard.api import router as dashboard_router`，并在其余 `include_router` 之后加 `app.include_router(dashboard_router, prefix="/api/v1")`。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_dashboard.py -v`
Expected: PASS（全部 4 个 Task 的测试通过）。

- [ ] **Step 5: Commit**

```bash
git add src/modules/dashboard/api.py src/main.py test/test_dashboard.py
git commit -m "feat: 工作台 API 路由与注册"
```

---

## 自检记录（Self-Review）

- **Spec 覆盖**：`01-工作台.md` 的 4 统计卡片（stats）、2 趋势图（trends）、Agent 排行榜（top-agents）、最近告警（recent-alerts）、资源用量（resource-usage）均有对应 Task；`types/dashboard.ts` 的 5 个接口字段在 Task 1 schema 中一一对应。
- **类型一致性**：`DashboardRepository` 的方法名/返回值在 Task 2 Produces 定义、Task 3 Consumes 引用、Task 3 service 方法在 Task 4 Consumes 引用，无命名漂移。
- **Review Focus**：5 条边界各有一条测试，分别落在 Task 3（空库/环比除零、7 天补全、成功率语义）、Task 2（缺失表降级）、Task 1（camelCase 契约）。
- **已知限制（写进计划，不做）**：`activeAgentsTrend` 恒为 0（无历史活跃 Agent 快照）；`存储空间`/`并发连接数` 的 used/total 为静态配置值（`Document.file_size` 是字符串无法可靠求和）。
