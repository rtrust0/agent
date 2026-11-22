# 数据统计（Analytics）模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从 0 新建后端 `src/modules/analytics/`，对 `conversations` 表做聚合统计，提供 6 个统计接口（总览/每日/按Agent/按模型/费用/评估），并把前端 analytics 服务层对齐到新接口与新类型。

**Architecture:** analytics 无独立业务表，Repository 直接用 SQLAlchemy 对 `conversations` 表做 `count/sum/avg/group by` 聚合（join `agents`/`models` 取名称），Service 层负责环比（当前期 vs 上期）、按日补零、百分比与预算等业务计算，API 层暴露 6 个 GET 接口。由于 `conversations` 表在仓库中尚不存在，Task 1 先以“最小聚合契约”落地该共享数据源（对话日志模块后续在同一张表上扩展 turns/trace）。响应字段使用 camelCase，逐字对应前端 `app/src/services/types/analytics.ts`。

**Tech Stack:** Python 3.13、FastAPI、SQLAlchemy 2.0 async（asyncmy 生产 / aiosqlite 测试）、Pydantic v2、pytest + pytest-asyncio、Alembic；前端 React 19 + TypeScript 5.9 + Vite。

**Spec:**
- `app/docs/08-数据统计.md`（用量/费用/评估三页指标与布局）
- `app/docs/10-API接口规范.md`（数据统计节：6 个接口）
- `app/src/services/types/analytics.ts`（前端类型，字段名/类型的权威来源）
- `docs/PROJECT_SPEC.md`（模块/分层/响应约定）

## Global Constraints

- 后端路由统一经 `src/main.py` 的 `app.include_router(router, prefix="/api/v1")` 注册；analytics 路由自身 `prefix="/analytics"`，最终路径形如 `GET /api/v1/analytics/overview`。
- 统一响应：`ResponseSchema`（`src/core/base_schema.py`）：`code: int = 200`、`message: str = "success"`、`data: Optional[T]`；业务异常 `BizException(code, message)`（`src/core/exceptions.py`）由全局处理器返回 HTTP 200 + `{"code":..., "message":..., "data": null}`。
- ORM 表字段 snake_case；ORM 继承 `BaseModel`（`src/core/base_model.py`，自带 `id` BigInteger 主键 + `created_at`/`updated_at`）。
- **analytics 响应字段一律 camelCase**，逐字与 `app/src/services/types/analytics.ts` 一致（这是 analytics 模块相对其它模块 snake_case 约定的唯一例外）。
- 认证：6 个接口均 `Depends(get_current_user)`（`src/core/deps.py`，JWT 校验）；RBAC 权限码清单中无 analytics 权限码，故不做 `get_current_user_with_permission` 拦截。
- 分页不适用于 analytics：不做 `PageParams`，日期通过 query 参数 `range`/`start_date`/`end_date` 注入。
- 测试：pytest + pytest-asyncio（`@pytest.mark.asyncio`），文件放 `/test/`，命令 `pytest test/xxx.py::test_name`；测试用 SQLite 内存库（`aiosqlite==0.22.1` 已在 requirements）。
- 每步 commit 消息用中文摘要（如 `feat: 数据统计模型创建`）。
- 前端 `apiClient.get` 自动解包响应 `data` 字段、自动注入 JWT、`code!==200` 时抛错（`app/src/services/api/client.ts`），故前端 api 服务返回类型是解包后的类型（如 `AnalyticsOverview`，非 `ResponseSchema<...>`）。

## Review Focus

1. **空数据（时间段内 0 条会话）**：所有聚合应返回 0/空列表而非 NaN 或除零异常——`avgLatency=0`、`successRate=0`、`trend=0`、`costByModel/costByAgent=[]`、`budgetRemaining=MONTHLY_BUDGET`、`daily` 返回按日补零的完整列表。→ 测试 `test_overview_empty_range_returns_zeros`（Task 4）。
2. **环比除零**：上期总量为 0 时 `*Trend` 应返回 `0.0`，不抛 `ZeroDivisionError`、不返回 `None`。→ 测试 `test_overview_trend_prev_zero_returns_zero`（Task 4）。
3. **agent_id / model_id 为 NULL（会话未绑定）**：by-agent/by-model 应把未绑定会话归入“未绑定”组（`agentId`/`modelId` 返回空串 `""`、名称 `"未绑定"`），不因 `NULL` join 崩溃或丢数据。→ 测试 `test_by_agent_unassigned_group`（Task 4）。
4. **日期边界**：`start_date == end_date` 时返回 1 天（含当天）；`end_date` 作为排他上界（`< end+1day`），避免漏掉当天 23:59 数据。→ 测试 `test_daily_single_day_boundary`（Task 4）。
5. **标注字段为 NULL**：`rating`/`satisfaction`/`tags` 为 NULL 的会话不进入 `avgRating`/`avgSatisfaction` 的分母；全 NULL 时 `avgRating=0`、`avgSatisfaction=0`；`annotationCoverage` 分母为全部会话数。→ 测试 `test_evaluation_null_annotation_excluded`（Task 4）。

---

### Task 1: conversations 表最小聚合契约（共享数据源 bootstrap）

> 说明：这是 analytics 的**前置依赖**。对话日志模块尚未实现，故先落地一张可支撑全部 6 个聚合接口的 `conversations` 表；对话日志模块后续在同一张表上扩展 `conversation_turns`/trace 等字段（本计划只建 analytics 所需字段）。

**Files:**
- Create: `src/modules/conversation/__init__.py`
- Create: `src/modules/conversation/model.py`
- Modify: `alembic/env.py`（在 `import src.modules.agent.model` 之后新增 `import src.modules.conversation.model`）
- Create: `alembic/versions/xxxx_创建conversations表.py`（`alembic revision --autogenerate -m "创建conversations表"` 生成）
- Create: `test/conftest.py`（共享 `db_session` fixture，供 `test_analytics.py` 与 `test_analytics_api.py` 复用）
- Test: `test/test_analytics.py`

**Interfaces:**
- Produces: `Conversation` ORM 类（`src.modules.conversation.model.Conversation`），字段如下（聚合契约，逐列精确）：

```python
class Conversation(BaseModel):
    __tablename__ = "conversations"

    agent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    model_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="completed")   # active/completed/error
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Numeric(12, 4), default=0)          # 人民币
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)             # 总耗时（毫秒）
    satisfaction: Mapped[str | None] = mapped_column(String(20), nullable=True)  # positive/negative
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)      # 标注评分 1-5
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)          # 标注标签列表（常见问题来源）
    needs_optimization: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)  # 时间范围过滤与按日分组依据
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

- Produces: pytest fixture `db_session`（`test/conftest.py` 内定义）：`@pytest_asyncio.fixture`，用 `create_async_engine("sqlite+aiosqlite:///:memory:")` 建库，`async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)`（仅需 import `src.modules.conversation.model`、`src.modules.agent.model`、`src.modules.model.model`，使 metadata 含 conversations/agents/agent_versions/models/model_providers 五张表），`async_sessionmaker(engine, expire_on_commit=False)` 创建并 `yield` 一个 `AsyncSession`，结束后 `await engine.dispose()`。

- [ ] **Step 1: 写失败测试** 创建 `test/conftest.py`：

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.base_model import Base
import src.modules.conversation.model  # noqa
import src.modules.agent.model  # noqa
import src.modules.model.model  # noqa

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()
```

  再创建 `test/test_analytics.py`：

```python
import pytest
from sqlalchemy import text

@pytest.mark.asyncio
async def test_conversation_model_create(db_session):
    from src.modules.conversation.model import Conversation
    db_session.add(Conversation(agent_id=None, model_id=None, status="completed",
                                input_tokens=100, output_tokens=50, cost=0.12,
                                latency_ms=2300, satisfaction="positive", rating=5,
                                tags=["准确"], needs_optimization=False))
    await db_session.commit()
    assert (await db_session.execute(text("SELECT COUNT(*) FROM conversations"))).scalar() == 1
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_analytics.py::test_conversation_model_create -v`
Expected: FAIL（`ModuleNotFoundError: src.modules.conversation` 或建表失败）

- [ ] **Step 3: 实现** 创建 `src/modules/conversation/model.py`（上述 `Conversation` 定义 + `from src.core.base_model import BaseModel` + 必要 import），`src/modules/conversation/__init__.py`（空），并在 `alembic/env.py` 增加 `import src.modules.conversation.model`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_analytics.py::test_conversation_model_create -v`
Expected: PASS

- [ ] **Step 5: 生成迁移并 commit**

```bash
alembic revision --autogenerate -m "创建conversations表"
alembic upgrade head
git add src/modules/conversation alembic/env.py alembic/versions test/conftest.py test/test_analytics.py
git commit -m "feat: conversations 聚合契约模型创建"
```

---

### Task 2: analytics Pydantic Schema（响应模型）

**Files:**
- Create: `src/modules/analytics/__init__.py`
- Create: `src/modules/analytics/schema.py`
- Test: `test/test_analytics.py`（追加）

**Interfaces:**
- Produces（字段名/类型逐字对应 `app/src/services/types/analytics.ts`，全部 camelCase）：

```python
class AnalyticsOverview(BaseModel):
    totalCalls: int; totalTokens: int; totalCost: float; avgLatency: float
    callsTrend: float; tokensTrend: float; costTrend: float; latencyTrend: float

class DailyStats(BaseModel):
    date: str          # "YYYY-MM-DD"
    calls: int; inputTokens: int; outputTokens: int; cost: float
    avgLatency: float  # 秒
    successRate: float # 0-100

class AgentAnalytics(BaseModel):
    agentId: str; agentName: str; calls: int; tokens: int
    cost: float; successRate: float; avgLatency: float

class ModelAnalytics(BaseModel):
    modelId: str; modelName: str; calls: int
    inputTokens: int; outputTokens: int; cost: float

class CostByModel(BaseModel): model: str; cost: float
class CostByAgent(BaseModel): agent: str; cost: float

class CostAnalysis(BaseModel):
    monthCost: float; dailyAvgCost: float; projectedCost: float; budgetRemaining: float
    costByModel: list[CostByModel]; costByAgent: list[CostByAgent]

class AgentEvaluation(BaseModel):
    agentId: str; agentName: str; satisfaction: float; avgRating: float
    annotationCount: int; needsOptimization: int
    trend: Literal["up", "down", "stable"]

class CommonIssue(BaseModel):
    type: str; count: int; percentage: float; trend: Literal["up", "down", "stable"]

class Evaluation(BaseModel):
    avgSatisfaction: float; annotationCoverage: float; needsOptimization: int; avgRating: float
    agentEvaluations: list[AgentEvaluation]; commonIssues: list[CommonIssue]

class AnalyticsQuery:  # 纯数据类，非 FastAPI 参数；service 入参
    range: str = "30d"                     # 允许值：1d/7d/30d/month/last-month/quarter/year
    start_date: date | None = None
    end_date: date | None = None
```

- [ ] **Step 1: 写失败测试** 追加：

```python
def test_analytics_schema_camel_case_keys():
    from src.modules.analytics.schema import AnalyticsOverview, Evaluation
    o = AnalyticsOverview(totalCalls=10, totalTokens=100, totalCost=1.5, avgLatency=2.3,
                          callsTrend=12.5, tokensTrend=0.0, costTrend=-3.2, latencyTrend=0.0)
    assert set(o.model_dump().keys()) == {"totalCalls","totalTokens","totalCost","avgLatency",
                                          "callsTrend","tokensTrend","costTrend","latencyTrend"}
    e = Evaluation(avgSatisfaction=92.0, annotationCoverage=45.0, needsOptimization=23,
                   avgRating=4.2, agentEvaluations=[], commonIssues=[])
    assert e.model_dump()["avgSatisfaction"] == 92.0
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_analytics.py::test_analytics_schema_camel_case_keys -v`
Expected: FAIL（`ModuleNotFoundError: src.modules.analytics`）

- [ ] **Step 3: 实现** 创建 `src/modules/analytics/schema.py`（上述模型；`from typing import Literal`、`from datetime import date`、`from pydantic import BaseModel`）。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_analytics.py::test_analytics_schema_camel_case_keys -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modules/analytics/schema.py src/modules/analytics/__init__.py test/test_analytics.py
git commit -m "feat: 数据统计 Pydantic 响应模型创建"
```

---

### Task 3: analytics Repository（聚合查询）

**Files:**
- Create: `src/modules/analytics/repository.py`
- Test: `test/test_analytics.py`（追加）

**Interfaces:**
- Consumes: `Conversation`（Task 1）、`Agent`（`src.modules.agent.model`）、`LLMModel`（`src.modules.model.model`）、`AsyncSession`。
- Produces（dataclass，定义在 `repository.py`；`start`/`end` 为 `datetime`，`end` 为排他上界；`latency_ms_sum` 为浮点累加）：

```python
@dataclass
class OverviewAgg: calls: int; tokens: int; cost: float; latency_ms_sum: float; latency_count: int
@dataclass
class DailyAgg: date: str; calls: int; input_tokens: int; output_tokens: int; cost: float; latency_ms_sum: float; completed: int; total: int
@dataclass
class AgentAgg: agent_id: int | None; agent_name: str | None; calls: int; tokens: int; cost: float; latency_ms_sum: float; completed: int; total: int
@dataclass
class ModelAgg: model_id: int | None; model_name: str | None; calls: int; input_tokens: int; output_tokens: int; cost: float
@dataclass
class EvalTotals: conversations: int; annotated: int; satisfaction_positive: int; satisfaction_total: int; rating_sum: int; rating_count: int; needs_optimization: int
@dataclass
class EvalAgentAgg: agent_id: int | None; agent_name: str | None; satisfaction_positive: int; satisfaction_total: int; rating_sum: int; rating_count: int; annotation_count: int; needs_optimization: int

class AnalyticsRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession): super().__init__(Conversation, db)

    async def overview(self, start: datetime, end: datetime) -> OverviewAgg: ...
    async def daily(self, start: datetime, end: datetime) -> list[DailyAgg]: ...
    async def by_agent(self, start: datetime, end: datetime) -> list[AgentAgg]: ...
    async def by_model(self, start: datetime, end: datetime) -> list[ModelAgg]: ...
    async def eval_totals(self, start: datetime, end: datetime) -> EvalTotals: ...
    async def eval_by_agent(self, start: datetime, end: datetime) -> list[EvalAgentAgg]: ...
    async def issue_counts(self, start: datetime, end: datetime) -> dict[str, int]: ...
```

- 聚合口径（实现时唯一采用，写入步骤）：过滤 `Conversation.started_at >= start AND < end`；`tokens = input_tokens + output_tokens`；`completed = COUNT(status='completed')`；`latency_count = COUNT(latency_ms > 0)`（用于平均延迟分母，避免把未完成/0 耗时计入）；按日分组用 `func.date(Conversation.started_at)`；by_agent/by_model 用 `func.count/sum/avg` 与 `Agent.name`/`LLMModel.name` 左连接，`NULL` 组名保留为 `None`；`annotated = COUNT(rating IS NOT NULL)`；`issue_counts` 对每行的 `tags`（JSON 列表）在 Python 侧展开计数。

- [ ] **Step 1: 写失败测试** 追加（fixture 复用 `db_session`；先 seed：1 个 Agent、1 个 LLMModel、3 条 Conversation 分布于两天，含一条 `status="error"`、一条 `agent_id=None`、一条带 `tags=["不准确"]`）：

```python
@pytest.mark.asyncio
async def test_repo_overview_daily_agent_model_aggregates(db_session):
    from datetime import datetime
    from src.modules.agent.model import Agent
    from src.modules.model.model import LLMModel
    from src.modules.conversation.model import Conversation
    from src.modules.analytics.repository import AnalyticsRepository
    a = Agent(name="智能客服", type="conversation", status="active"); db_session.add(a)
    m = LLMModel(name="GPT-4", model_id="gpt-4", provider_id=1); db_session.add(m)
    await db_session.flush()
    db_session.add_all([
        Conversation(agent_id=a.id, model_id=m.id, status="completed", input_tokens=100, output_tokens=50, cost=1.0, latency_ms=2000, started_at=datetime(2024,2,1,10,0)),
        Conversation(agent_id=a.id, model_id=m.id, status="completed", input_tokens=200, output_tokens=100, cost=2.0, latency_ms=4000, started_at=datetime(2024,2,2,10,0)),
        Conversation(agent_id=None, model_id=None, status="error", input_tokens=10, output_tokens=0, cost=0.0, latency_ms=0, started_at=datetime(2024,2,2,11,0), tags=["不准确"]),
    ])
    await db_session.commit()
    repo = AnalyticsRepository(db_session)
    ov = await repo.overview(datetime(2024,2,1), datetime(2024,2,3))
    assert ov.calls == 3 and ov.tokens == 460 and ov.cost == 3.0
    daily = await repo.daily(datetime(2024,2,1), datetime(2024,2,3))
    assert {d.date: d.calls for d in daily} == {"2024-02-01": 1, "2024-02-02": 2}
    agents = await repo.by_agent(datetime(2024,2,1), datetime(2024,2,3))
    assert any(x.agent_id is None for x in agents) and any(x.agent_name == "智能客服" for x in agents)
    models = await repo.by_model(datetime(2024,2,1), datetime(2024,2,3))
    assert any(x.model_name == "GPT-4" and x.input_tokens == 300 and x.output_tokens == 150 for x in models)
    totals = await repo.eval_totals(datetime(2024,2,1), datetime(2024,2,3))
    assert totals.conversations == 3
    issues = await repo.issue_counts(datetime(2024,2,1), datetime(2024,2,3))
    assert issues == {"不准确": 1}
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_analytics.py::test_repo_overview_daily_agent_model_aggregates -v`
Expected: FAIL（`ModuleNotFoundError: src.modules.analytics.repository`）

- [ ] **Step 3: 实现** `src/modules/analytics/repository.py`：按上述 dataclass 与聚合口径实现 7 个方法（`select(func.count()...).where(...)` / `group_by` / `outerjoin`；`func.date` 在 MySQL 与 SQLite 均可用）。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_analytics.py::test_repo_overview_daily_agent_model_aggregates -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modules/analytics/repository.py test/test_analytics.py
git commit -m "feat: 数据统计聚合查询 repository 完成"
```

---

### Task 4: analytics Service（环比 / 补零 / 百分比 / 预算）

**Files:**
- Create: `src/modules/analytics/service.py`
- Test: `test/test_analytics.py`（追加）

**Interfaces:**
- Consumes: `AnalyticsRepository`（Task 3）、schema 模型（Task 2）、`AnalyticsQuery`。
- Produces:

```python
MONTHLY_BUDGET: float = 50000.0  # 月度预算常量（无预算表，后续迁移到系统配置）

class AnalyticsService:
    def __init__(self, db: AsyncSession): self.repo = AnalyticsRepository(db)

    async def get_overview(self, q: AnalyticsQuery) -> AnalyticsOverview: ...
    async def get_daily(self, q: AnalyticsQuery) -> list[DailyStats]: ...
    async def get_by_agent(self, q: AnalyticsQuery) -> list[AgentAnalytics]: ...
    async def get_by_model(self, q: AnalyticsQuery) -> list[ModelAnalytics]: ...
    async def get_costs(self, q: AnalyticsQuery) -> CostAnalysis: ...
    async def get_evaluation(self, q: AnalyticsQuery) -> Evaluation: ...

    def _resolve_range(self, q: AnalyticsQuery) -> tuple[datetime, datetime, datetime, datetime]:
        # 返回 (cur_start, cur_end_exclusive, prev_start, prev_end_exclusive)
```

- 口径（写入步骤，唯一实现）：`_resolve_range`：`start_date`/`end_date` 都给定时，`cur=[start_date 00:00, end_date+1day 00:00)`，`L=(end_date-start_date).days+1`，`prev=[start_date-L, start_date)`；否则按 `range` 预设（`1d`=今天、`7d`/`30d`=含今天往前 N 天、`month`/`last-month`/`quarter`/`year` 用 `date.today()` 对应日历周期），`prev` 为等长紧邻上期。所有边界为当日 `00:00:00`。
- 趋势公式：`trend = round((cur - prev) / prev * 100, 1) if prev else 0.0`；`avgLatency(秒) = round((latency_ms_sum / latency_count) / 1000, 2) if latency_count else 0.0`；`successRate = round(completed / total * 100, 1) if total else 0.0`。
- `get_daily`：`repo.daily` 结果转 dict 后，对 `cur_start..<cur_end` 逐日生成 `DailyStats`（缺天补零），`date` 用 `strftime("%Y-%m-%d")`。
- `get_by_agent`/`get_by_model`：`agentId = "" if agent_id is None else str(agent_id)`；`agentName = agent_name or "未绑定"`；`modelId`/`modelName` 同规则；按 `tokens`（by_agent）与 `cost`（by_model）降序。
- `get_costs`：`monthCost = repo.overview().cost`；`dailyAvgCost = monthCost / 期间天数`（期间天数=0 时取 0）；`projectedCost = round(dailyAvgCost * days_in_current_month, 2)`（`calendar.monthrange(end 所在年/月)`）；`budgetRemaining = round(max(MONTHLY_BUDGET - monthCost, 0.0), 2)`；`costByModel`/`costByAgent` 复用 `by_model`/`by_agent` 的 cost，字段 `model`/`agent` = 名称，降序。
- `get_evaluation`：`avgSatisfaction = round(satisfaction_positive / satisfaction_total * 100, 1) if satisfaction_total else 0.0`；`avgRating = round(rating_sum / rating_count, 1) if rating_count else 0.0`；`annotationCoverage = round(annotated / conversations * 100, 1) if conversations else 0.0`；`needsOptimization = needs_optimization`；`agentEvaluations` 来自 `eval_by_agent`（当前期），`trend` 由当前期满意度 vs 上期同 agent 满意度比较：`up`(>1)、`down`(<-1)、否则 `stable`；`commonIssues` 来自 `issue_counts`（当前期 vs 上期 count 比较得 trend），`percentage = round(count / total_count * 100, 1)`，按 count 降序。

- [ ] **Step 1: 写失败测试** 追加（seed 见下；固定 `AnalyticsQuery(start_date=date(2024,2,1), end_date=date(2024,2,7))`）：

```python
@pytest.mark.asyncio
async def test_overview_empty_range_returns_zeros(db_session):
    from datetime import date
    from src.modules.analytics.service import AnalyticsService
    from src.modules.analytics.schema import AnalyticsQuery
    svc = AnalyticsService(db_session)
    o = await svc.get_overview(AnalyticsQuery(start_date=date(2024,1,1), end_date=date(2024,1,7)))
    assert o.totalCalls == 0 and o.totalCost == 0.0 and o.avgLatency == 0.0
    assert o.callsTrend == 0.0 and o.tokensTrend == 0.0 and o.costTrend == 0.0 and o.latencyTrend == 0.0

@pytest.mark.asyncio
async def test_overview_trend_prev_zero_returns_zero(db_session):
    # 仅当前期有 1 条会话，上期为空
    from datetime import date, datetime
    from src.modules.conversation.model import Conversation
    from src.modules.analytics.service import AnalyticsService
    from src.modules.analytics.schema import AnalyticsQuery
    db_session.add(Conversation(status="completed", input_tokens=100, output_tokens=50, cost=1.0, latency_ms=2000, started_at=datetime(2024,2,1,10,0)))
    await db_session.commit()
    o = await AnalyticsService(db_session).get_overview(AnalyticsQuery(start_date=date(2024,2,1), end_date=date(2024,2,7)))
    assert o.callsTrend == 0.0 and o.costTrend == 0.0

@pytest.mark.asyncio
async def test_by_agent_unassigned_group(db_session):
    from datetime import date, datetime
    from src.modules.conversation.model import Conversation
    from src.modules.analytics.service import AnalyticsService
    from src.modules.analytics.schema import AnalyticsQuery
    db_session.add(Conversation(agent_id=None, model_id=None, status="completed", input_tokens=10, output_tokens=0, cost=0.0, latency_ms=1000, started_at=datetime(2024,2,1,10,0)))
    await db_session.commit()
    rows = await AnalyticsService(db_session).get_by_agent(AnalyticsQuery(start_date=date(2024,2,1), end_date=date(2024,2,7)))
    assert len(rows) == 1 and rows[0].agentId == "" and rows[0].agentName == "未绑定"

@pytest.mark.asyncio
async def test_daily_single_day_boundary(db_session):
    from datetime import date, datetime
    from src.modules.conversation.model import Conversation
    from src.modules.analytics.service import AnalyticsService
    from src.modules.analytics.schema import AnalyticsQuery
    db_session.add(Conversation(status="completed", input_tokens=10, output_tokens=5, cost=0.1, latency_ms=1000, started_at=datetime(2024,2,1,23,50)))
    await db_session.commit()
    daily = await AnalyticsService(db_session).get_daily(AnalyticsQuery(start_date=date(2024,2,1), end_date=date(2024,2,1)))
    assert len(daily) == 1 and daily[0].date == "2024-02-01" and daily[0].calls == 1

@pytest.mark.asyncio
async def test_evaluation_null_annotation_excluded(db_session):
    from datetime import date, datetime
    from src.modules.conversation.model import Conversation
    from src.modules.analytics.service import AnalyticsService
    from src.modules.analytics.schema import AnalyticsQuery
    db_session.add_all([
        Conversation(status="completed", rating=5, satisfaction="positive", started_at=datetime(2024,2,1,10,0)),
        Conversation(status="completed", rating=None, satisfaction=None, started_at=datetime(2024,2,1,11,0)),
    ])
    await db_session.commit()
    e = await AnalyticsService(db_session).get_evaluation(AnalyticsQuery(start_date=date(2024,2,1), end_date=date(2024,2,7)))
    assert e.avgRating == 5.0 and e.annotationCoverage == 50.0 and e.avgSatisfaction == 100.0
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_analytics.py -k "empty_range or trend_prev_zero or unassigned_group or single_day_boundary or null_annotation" -v`
Expected: FAIL（`ModuleNotFoundError: src.modules.analytics.service`）

- [ ] **Step 3: 实现** `src/modules/analytics/service.py`：按上述签名与口径实现（`from calendar import monthrange`、`from datetime import date, datetime, time, timedelta`）。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_analytics.py -v`
Expected: 全 PASS（含 Task 1–3 已通过用例）

- [ ] **Step 5: Commit**

```bash
git add src/modules/analytics/service.py test/test_analytics.py
git commit -m "feat: 数据统计 service 环比/补零/费用/评估计算完成"
```

---

### Task 5: analytics API 路由 + main.py 注册

**Files:**
- Create: `src/modules/analytics/api.py`
- Modify: `src/main.py`（import + `app.include_router(analytics_router, prefix="/api/v1")`）
- Test: `test/test_analytics_api.py`

**Interfaces:**
- Consumes: `AnalyticsService`、`AnalyticsQuery`、`ResponseSchema`、`get_current_user`、`get_db`。
- Produces（6 个路由，均 `response_model=ResponseSchema[...]`；query 参数统一 `range_: str = Query("30d", alias="range")`、`start_date: date | None = Query(None)`、`end_date: date | None = Query(None)`，即请求串键名为 `range`/`start_date`/`end_date`）：

```python
router = APIRouter(prefix="/analytics", tags=["数据统计"])

def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService: ...

GET /analytics/overview    -> ResponseSchema[AnalyticsOverview]
GET /analytics/daily       -> ResponseSchema[list[DailyStats]]
GET /analytics/by-agent    -> ResponseSchema[list[AgentAnalytics]]
GET /analytics/by-model    -> ResponseSchema[list[ModelAnalytics]]
GET /analytics/costs       -> ResponseSchema[CostAnalysis]
GET /analytics/evaluation  -> ResponseSchema[Evaluation]
```

  每个 handler：`AnalyticsQuery(range=range_, start_date=start_date, end_date=end_date)` 构造后调 `svc.get_xxx(q)`，返回 `ResponseSchema(data=result)`；handler 依赖 `Depends(get_current_user)` 与 `Depends(get_analytics_service)`。

- [ ] **Step 1: 写失败测试** `test/test_analytics_api.py`：

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.infra.database import get_db
from src.core.deps import get_current_user

@pytest.mark.asyncio
async def test_analytics_endpoints_ok(db_session):
    async def override_db():
        yield db_session
    async def override_user():
        return None
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path, key in [
            ("/api/v1/analytics/overview", "totalCalls"),
            ("/api/v1/analytics/daily", None),           # 应为 list
            ("/api/v1/analytics/by-agent", None),
            ("/api/v1/analytics/by-model", None),
            ("/api/v1/analytics/costs", "monthCost"),
            ("/api/v1/analytics/evaluation", "avgSatisfaction"),
        ]:
            r = await client.get(path, params={"start_date": "2024-02-01", "end_date": "2024-02-07"})
            assert r.status_code == 200
            body = r.json()
            assert body["code"] == 200
            if key:
                assert key in body["data"]
            else:
                assert isinstance(body["data"], list)
    app.dependency_overrides.clear()
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_analytics_api.py::test_analytics_endpoints_ok -v`
Expected: FAIL（`ModuleNotFoundError: src.modules.analytics.api` 或 404 路由未注册）

- [ ] **Step 3: 实现** 创建 `src/modules/analytics/api.py`，并在 `src/main.py` 增加 `from src.modules.analytics.api import router as analytics_router` 与 `app.include_router(analytics_router, prefix="/api/v1")`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_analytics_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modules/analytics/api.py src/main.py test/test_analytics_api.py
git commit -m "feat: 数据统计 6 个统计接口路由完成并注册"
```

---

### Task 6: 前端 analytics 服务层对齐到新接口/新类型

**Files:**
- Modify: `app/src/services/api/analytics.ts`
- Modify: `app/src/services/mock/analytics.ts`
- Modify: `app/src/services/mock/data/analytics.ts`
- Modify: `app/src/pages/analytics/Usage.tsx`
- Modify: `app/src/pages/analytics/Costs.tsx`
- Modify: `app/src/pages/analytics/Evaluation.tsx`
- Test: `cd app && npm run build`（`tsc -b` 类型检查）

**Interfaces:**
- Consumes: `app/src/services/types/analytics.ts`（已就绪，勿改）、`apiClient`（自动解包 `data`）。
- Produces（`apiAnalyticsService` 与 `mockAnalyticsService` 同签名，`services/analytics.ts` 开关不变）：

```ts
getOverview(params?: { range?: string; startDate?: string; endDate?: string }): Promise<AnalyticsOverview>
getDaily(params?): Promise<DailyStats[]>
getByAgent(params?): Promise<AgentAnalytics[]>
getByModel(params?): Promise<ModelAnalytics[]>
getCosts(params?): Promise<CostAnalysis>
getEvaluation(params?): Promise<Evaluation>
```

  api 层路径：`getOverview`→`GET /analytics/overview`、`getDaily`→`/analytics/daily`、`getByAgent`→`/analytics/by-agent`、`getByModel`→`/analytics/by-model`、`getCosts`→`/analytics/costs`、`getEvaluation`→`/analytics/evaluation`；`startDate`/`endDate` 在请求中映射为 `start_date`/`end_date`，`range` 原样传。移除旧方法 `getUsageStats`/`getCostStats`/`getEvaluationStats`/`exportReport`（导出报表不在本计划范围）。`mock/data/analytics.ts` 改为导出 `mockOverview`/`mockDaily`/`mockByAgent`/`mockByModel`/`mockCosts`/`mockEvaluation`（字段名对齐新类型）。

- 页面改造口径（不写 JSX，只锁字段对应）：
  - `Usage.tsx`：`analyticsService.getOverview({ range: period })` 渲染 4 张卡（`totalCalls`/`totalTokens`/`totalCost`/`avgLatency` + 4 个 `*Trend`），`getByAgent({range: period})` 渲染 Agent 表（`agentId/agentName/calls/tokens/cost/successRate/avgLatency`），`getByModel({range: period})` 渲染模型表（`modelId/modelName/calls/inputTokens/outputTokens/cost`）；可选渲染 `getDaily` 趋势图。
  - `Costs.tsx`：`getCosts({ range: period })` 渲染 4 张卡（`monthCost/dailyAvgCost/projectedCost/budgetRemaining`）与 `costByModel`/`costByAgent` 表格。
  - `Evaluation.tsx`：`getEvaluation()` 渲染 4 张卡（`avgSatisfaction/annotationCoverage/needsOptimization/avgRating`）、`agentEvaluations` 表格（含 `trend` 图标）、`commonIssues` 列表。

- [ ] **Step 1: 先改 `api/analytics.ts` 为 6 个新方法（此时 `tsc` 会因旧类型引用报错）**

- [ ] **Step 2: 运行确认类型错误**

Run: `cd app && npm run build`
Expected: 失败（页面与 mock 仍引用 `UsageStats`/`CostStats`/`EvaluationStats` 等已删除类型）

- [ ] **Step 3: 改造 `mock/analytics.ts`、`mock/data/analytics.ts` 与 3 个页面到新类型/新方法**

按上述口径替换；删除对 `UsageStats/CostStats/EvaluationStats` 的所有引用（`rg "UsageStats|CostStats|EvaluationStats" app/src` 应无结果）。

- [ ] **Step 4: 运行确认通过**

Run: `cd app && npm run build`
Expected: `tsc -b` 无错误，vite build 成功

- [ ] **Step 5: Commit**

```bash
git add app/src/services/api/analytics.ts app/src/services/mock/analytics.ts app/src/services/mock/data/analytics.ts app/src/pages/analytics
git commit -m "feat: 前端 analytics 服务层对齐新统计接口与类型"
```
