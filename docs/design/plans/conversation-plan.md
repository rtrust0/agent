# 对话日志（Conversation）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从零新建后端 `src/modules/conversation/` 五层模块，提供对话日志的查询（分页+多条件筛选）、详情、轮次列表、链路追踪读取、标注与导出接口。

**Architecture:** 沿用仓库既有 5 层架构（model → schema → repository → service → api）。`Conversation` 与 `ConversationTurn` 两张表，`TraceStep` 不单独建表、整体存入 `conversation_turns.trace` JSON 列；标注整体存入 `conversations.annotation` JSON 列。conversation 无独立 CRUD 创建入口（对话由运行时产生），本模块只覆盖查询、标注、导出；model 层保留可实例化能力供未来运行时写入。

**Tech Stack:** Python 3.13 + FastAPI + SQLAlchemy 2.0 async（asyncmy）、Pydantic v2、Alembic、pytest + pytest-asyncio（测试用 aiosqlite 内存库）。

**Spec:**
- 项目说明 V1：`docs/PROJECT_SPEC.md`
- 项目说明 V2（RBAC 授权）：`docs/spec/PROJECT_SPEC_V2.md`
- 模块设计文档（对话日志）：`app/docs/07-对话日志.md`
- API 接口规范（对话日志节）：`app/docs/10-API接口规范.md`
- 前端类型（字段权威来源）：`app/src/services/types/conversation.ts`
- 前端 API 服务（实际调用路径）：`app/src/services/api/conversation.ts`

## Global Constraints

以下项目级约束对所有 Task 隐式生效，逐条精确值：

1. 路由统一 `/api/v1` 前缀；本模块定义两个 router：`router`（`prefix="/conversations"`）与 `turn_router`（`prefix="/turns"`），均在 `src/main.py` 用 `app.include_router(..., prefix="/api/v1")` 注册。
2. 响应统一 `ResponseSchema(code=200, message="success", data=...)`（`src/core/base_schema.py`）；分页统一 `PageResult(items, total, page, page_size)`。
3. 分页参数 `PageParams(page 从1起, page_size 默认10 上限100, keyword)`（`src/core/deps.py`），通过 `Depends()` 注入。
4. 业务异常抛 `BizException(code, message)`（`src/core/exceptions.py`），全局异常处理器返回 HTTP 200 + `{"code":..., "message":..., "data":null}`。
5. 认证：所有接口 `Depends(get_current_user)`（JWT 校验，`src/core/deps.py`）；标注接口额外取 `current_user.username` 作为 `annotatedBy`。
6. ORM 继承 `BaseModel`（`src/core/base_model.py`，含自增 `BigInteger id`、`created_at`、`updated_at`）；JSON 列用 `mapped_column(JSON)`；金额用 `Numeric(12, 6)` 并在 Read 转 `float`。
7. 后端表字段/ORM/Pydantic 均用 snake_case；JSON 列内部键用 camelCase（与前端嵌套类型逐字一致）。字段映射表（前端 `types/conversation.ts` 权威，类型一一对应）：

   | 前端字段 | 后端字段 | 类型 |
   |---|---|---|
   | `id: string` | `id` | `int`（BigInt 自增，JSON 序列化为数字） |
   | `agentId: string` | `agent_id` | `str` |
   | `agentName: string` | `agent_name` | `str` |
   | `userId: string` | `user_id` | `str` |
   | `status: 'active'\|'completed'\|'error'` | `status` | `str` |
   | `turnCount: number` | `turn_count` | `int` |
   | `totalTokens: number` | `total_tokens` | `int` |
   | `totalCost: number` | `total_cost` | `float`（Numeric(12,6)） |
   | `totalDuration: number` | `total_duration` | `int`（毫秒） |
   | `satisfaction?: 'positive'\|'negative'\|null` | `satisfaction` | `str \| None`（字符串枚举，不是数字） |
   | `startedAt: string` | `started_at` | `datetime` |
   | `endedAt?: string` | `ended_at` | `datetime \| None` |
   | `turns`（详情） | `turns` | `list[ConversationTurnRead]` |
   | `annotation?`（详情） | `annotation` | `dict \| None`（JSON） |

   `ConversationTurn` 映射：`id`→`id:int`、`role:'user'|'assistant'`→`role:str`、`content:string`→`content:str(Text)`、`timestamp:string`→`timestamp:datetime`、`trace?`→`trace:dict|None(JSON)`，另加 `position:int`（序号，仅后端排序用）。

8. `agent_id`/`user_id` 存字符串（无外键，快照式冗余，删 Agent/User 不级联删日志，与前端 string 类型一致）。
9. `annotation` JSON 键（camelCase，与前端 `ConversationAnnotation` 一致）：`rating:int(1-5)`、`tags:list[str]`、`notes:str`、`annotatedBy:str`、`annotatedAt:str(ISO)`。
10. `trace` JSON 键（camelCase，与前端 `TurnTrace` 一致）：`steps:list`、`inputTokens:int`、`outputTokens:int`、`totalDuration:int(ms)`、`model:str`；`steps` 内元素键（`TraceStep`）：`type:str`、`name:str`、`duration:int(ms)`、`detail:dict`。
11. 业务错误码：`46001`「对话不存在」、`46002`「对话轮次不存在」、`46003`「不支持的导出格式」。
12. 导出接口为 `GET /conversations/{id}/export?format=json|txt`（以 `app/src/services/api/conversation.ts` 实际路径为准，覆盖 `10-API接口规范.md` 中的 `POST /conversations/export`）。
13. 提交消息格式：中文摘要（如 `feat: 对话日志模型创建`）。
14. 列表 item 返回前端 `Conversation` 字段（不含 `annotation`/`turns`）；详情返回 `ConversationDetail`（含 `turns`+`annotation`）。列表「标注状态」列由前端派生，后端只提供 `annotated` 布尔筛选。

## Review Focus

以下 5 类输入/边界最易踩坑，逐条对应到所属 Task 的测试：

1. `satisfaction` 是字符串枚举 `'positive'|'negative'|null`，不是数字（旧 mock 数据 `satisfaction: 5` 已过期）。→ Task 2 `test_conversation_read_from_attributes` 断言 satisfaction 为 `str|None`。
2. `total_duration` 单位是毫秒 int、`total_cost` 是小数金额（Numeric→float），导出时不得丢精度或误当秒。→ Task 4 `test_export_json` 断言 `total_duration`/`total_cost` 数值原样进入 JSON。
3. 导出 `format` 非 `json`/`txt` 必须抛 `BizException(400)`，不能落成 500。→ Task 4 `test_export_invalid_format_raises`。
4. `rating` 必须在 1..5，越界由 Pydantic 拒绝（请求 422），不能落库脏数据。→ Task 2 `test_annotate_request_rating_bounds`。
5. 查询不存在的对话/轮次必须返回业务码 `46001`/`46002`（HTTP 200 + code），不能返回空列表或 `None` 让前端误判为“无数据”。→ Task 4 `test_get_conversation_not_found_raises`、`test_get_trace_turn_not_found_raises`。

---

## File Structure

- Create: `src/modules/conversation/__init__.py` — 空文件，模块标记
- Create: `src/modules/conversation/model.py` — `Conversation`、`ConversationTurn` ORM
- Create: `src/modules/conversation/schema.py` — `ConversationFilter`、`ConversationAnnotateRequest`、`ConversationRead`、`ConversationTurnRead`、`ConversationDetailRead`
- Create: `src/modules/conversation/repository.py` — `ConversationRepository`、`ConversationTurnRepository`
- Create: `src/modules/conversation/service.py` — `ConversationService`（列表/详情/轮次/链路/标注/导出）
- Create: `src/modules/conversation/api.py` — `router`（/conversations）、`turn_router`（/turns）
- Modify: `src/main.py` — 导入并注册两个 router
- Modify: `alembic/env.py` — 追加 `import src.modules.conversation.model`
- Create: `alembic/versions/<hash>_创建conversations和conversation_turns表.py` — 迁移
- Create: `test/conftest.py` — aiosqlite 内存库 `db_session` fixture（Task 1 创建，后续复用）
- Test: `test/test_conversation.py` — 全部测试

---

### Task 1: ORM 模型 + Alembic 迁移

**Files:**
- Create: `src/modules/conversation/__init__.py`
- Create: `src/modules/conversation/model.py`
- Create: `test/conftest.py`
- Create: `alembic/versions/<hash>_创建conversations和conversation_turns表.py`（autogenerate 生成）
- Modify: `alembic/env.py:33-41`
- Test: `test/test_conversation.py`

**Interfaces:**
- Consumes: `src.core.base_model.BaseModel`（`id`/`created_at`/`updated_at`）；`sqlalchemy.orm.Mapped`、`mapped_column`。
- Produces:
  - `class Conversation(BaseModel)`：`__tablename__ = "conversations"`，字段 `agent_id: str`、`agent_name: str`、`user_id: str`、`status: str`、`turn_count: int`、`total_tokens: int`、`total_cost: Numeric`、`total_duration: int`、`satisfaction: str | None`、`annotation: dict | None`、`started_at: datetime`、`ended_at: datetime | None`，关系 `turns -> list[ConversationTurn]`（`order_by="ConversationTurn.position"`、`cascade="all, delete-orphan"`）。
  - `class ConversationTurn(BaseModel)`：`__tablename__ = "conversation_turns"`，字段 `conversation_id: int`（`ForeignKey("conversations.id", ondelete="CASCADE")`）、`position: int`、`role: str`、`content: str`、`timestamp: datetime`、`trace: dict | None`，关系 `conversation -> Conversation`。
  - `test/conftest.py` 中的 `db_session` 异步 fixture（aiosqlite 内存库，`Base.metadata.create_all`）。

- [ ] **Step 1: 写失败测试**

在 `test/test_conversation.py` 写 `test_conversation_models_registered`：

```python
from src.modules.conversation.model import Conversation, ConversationTurn
from src.core.base_model import BaseModel

def test_conversation_models_registered():
    assert Conversation.__tablename__ == "conversations"
    assert ConversationTurn.__tablename__ == "conversation_turns"
    assert issubclass(Conversation, BaseModel)
    assert issubclass(ConversationTurn, BaseModel)
    assert hasattr(Conversation, "agent_id")
    assert hasattr(ConversationTurn, "trace")
```

在 `test/conftest.py` 写 `db_session` fixture（`@pytest_asyncio.fixture`，用 `sqlite+aiosqlite:///:memory:`，`await conn.run_sync(Base.metadata.create_all)`，`yield session` 后 `engine.dispose()`）。

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_conversation.py::test_conversation_models_registered -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'src.modules.conversation'`

- [ ] **Step 3: 实现 `Conversation` 与 `ConversationTurn` 于 `src/modules/conversation/model.py`**

按上面 Produces 的字段与表名写 ORM；`total_cost` 用 `mapped_column(Numeric(12, 6), default=0, comment="总费用")`；`satisfaction` `String(20)` 可空；`trace`/`annotation` 用 `mapped_column(JSON, nullable=True)`；`conversation_id` 用 `BigInteger` + `ForeignKey`。创建空 `__init__.py`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_conversation.py::test_conversation_models_registered -v`
Expected: PASS

- [ ] **Step 5: 生成迁移并注册模型**

在 `alembic/env.py` 的模块导入区追加 `import src.modules.conversation.model`。然后运行 `alembic revision --autogenerate -m "创建conversations和conversation_turns表"`，确认生成的迁移含两张表与 FK。

- [ ] **Step 6: 应用迁移确认**

Run: `alembic upgrade head`
Expected: 无报错，`conversations`、`conversation_turns` 表创建成功

- [ ] **Step 7: Commit**

```bash
git add src/modules/conversation/__init__.py src/modules/conversation/model.py test/conftest.py test/test_conversation.py alembic/env.py alembic/versions/<hash>_创建conversations和conversation_turns表.py
git commit -m "feat: 对话日志模型创建"
```

---

### Task 2: Pydantic Schema

**Files:**
- Create: `src/modules/conversation/schema.py`
- Test: `test/test_conversation.py`

**Interfaces:**
- Consumes: Task 1 的 `Conversation`、`ConversationTurn`。
- Produces:
  - `class ConversationFilter(BaseModel)`：`agent_id: str | None = None`、`status: str | None = None`、`user_id: str | None = None`、`satisfaction: str | None = None`、`annotated: bool | None = None`、`started_from: datetime | None = None`、`started_to: datetime | None = None`。
  - `class ConversationAnnotateRequest(BaseModel)`：`rating: int = Field(ge=1, le=5)`、`tags: list[str] = []`、`notes: str = ""`。
  - `class ConversationRead(BaseModel)`（`model_config = {"from_attributes": True}`）：`id:int`、`agent_id:str`、`agent_name:str`、`user_id:str`、`status:str`、`turn_count:int`、`total_tokens:int`、`total_cost:float`、`total_duration:int`、`satisfaction:str|None`、`started_at:datetime`、`ended_at:datetime|None`、`created_at:datetime`、`updated_at:datetime`。
  - `class ConversationTurnRead(BaseModel)`（`from_attributes`）：`id:int`、`conversation_id:int`、`position:int`、`role:str`、`content:str`、`timestamp:datetime`、`trace:dict|None`。
  - `class ConversationDetailRead(ConversationRead)`：`turns: list[ConversationTurnRead] = []`、`annotation: dict | None = None`。

- [ ] **Step 1: 写失败测试**

在 `test/test_conversation.py` 写两个测试：

```python
import pytest
from pydantic import ValidationError
from src.modules.conversation.schema import ConversationAnnotateRequest, ConversationRead
from src.modules.conversation.model import Conversation

def test_annotate_request_rating_bounds():
    assert ConversationAnnotateRequest(rating=5, tags=["准确"]).rating == 5
    with pytest.raises(ValidationError):
        ConversationAnnotateRequest(rating=0)
    with pytest.raises(ValidationError):
        ConversationAnnotateRequest(rating=6)

def test_conversation_read_from_attributes():
    conv = Conversation(id=1, agent_id="agent-001", agent_name="智能客服",
                        user_id="user-001", status="completed", turn_count=3,
                        total_tokens=100, total_cost=0.0234, total_duration=45,
                        satisfaction="positive", started_at="2024-02-07T10:30:00")
    read = ConversationRead.model_validate(conv)
    assert read.satisfaction == "positive"
    assert read.total_duration == 45
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_conversation.py::test_annotate_request_rating_bounds -v`
Expected: FAIL，`ModuleNotFoundError`/`ImportError`（schema 未建）

- [ ] **Step 3: 实现 `src/modules/conversation/schema.py`**

按 Produces 定义五个 Pydantic 模型；`ConversationRead`/`ConversationTurnRead` 加 `model_config = {"from_attributes": True}`；`rating` 用 `Field(ge=1, le=5)`；`total_cost` 声明为 `float`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_conversation.py::test_annotate_request_rating_bounds test/test_conversation.py::test_conversation_read_from_attributes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modules/conversation/schema.py test/test_conversation.py
git commit -m "feat: 对话日志Schema定义"
```

---

### Task 3: Repository

**Files:**
- Create: `src/modules/conversation/repository.py`
- Test: `test/test_conversation.py`

**Interfaces:**
- Consumes: `src.core.base_repository.BaseRepository[T]`（`get_by_id`/`get_page`/`create`/`update`/`delete`）；Task 1 `Conversation`/`ConversationTurn`；Task 2 `ConversationFilter`。
- Produces:
  - `class ConversationRepository(BaseRepository[Conversation])`：类属性 `SEARCH_FIELDS = ["agent_name", "user_id"]`；`__init__(self, db: AsyncSession)`；`async def search_page(self, offset: int, limit: int, keyword: str | None, filters: ConversationFilter) -> tuple[list[Conversation], int]`。
  - `class ConversationTurnRepository(BaseRepository[ConversationTurn])`：`__init__(self, db: AsyncSession)`；`async def get_turns_by_conversation(self, conversation_id: int) -> list[ConversationTurn]`（按 `position` 升序）。

- [ ] **Step 1: 写失败测试**

在 `test/test_conversation.py` 写 `test_search_page_filters`（`@pytest.mark.asyncio`，注入 `db_session` fixture）：

```python
from datetime import datetime
from src.modules.conversation.repository import ConversationRepository
from src.modules.conversation.schema import ConversationFilter
from src.modules.conversation.model import Conversation

@pytest.mark.asyncio
async def test_search_page_filters(db_session):
    repo = ConversationRepository(db_session)
    await repo.create(Conversation(agent_id="a1", agent_name="客服", user_id="u1",
        status="completed", turn_count=2, total_tokens=10, total_cost=0.1,
        total_duration=100, satisfaction="positive", started_at=datetime(2024,2,7,10,0)))
    await repo.create(Conversation(agent_id="a2", agent_name="审查", user_id="u2",
        status="active", turn_count=5, total_tokens=20, total_cost=0.2,
        total_duration=200, satisfaction=None, started_at=datetime(2024,2,8,10,0)))
    items, total = await repo.search_page(0, 20, None,
        ConversationFilter(status="completed", satisfaction="positive"))
    assert total == 1
    assert items[0].agent_id == "a1"
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_conversation.py::test_search_page_filters -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'src.modules.conversation.repository'`

- [ ] **Step 3: 实现 `src/modules/conversation/repository.py`**

`search_page` 基于 `select(Conversation)` 依次叠加 WHERE：`agent_id`/`status`/`user_id`/`satisfaction` 等值；`annotated is True` → `annotation.isnot(None)`，`False` → `annotation.is_(None)`；`started_from`/`started_to` 用 `started_at >=` / `<=`；`keyword` 复用 `get_page` 的 `search_fields=self.SEARCH_FIELDS` 做 OR 模糊。总数用 `func.count()` 子查询，分页按 `id.asc()` 排序，返回 `(items, total)`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_conversation.py::test_search_page_filters -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modules/conversation/repository.py test/test_conversation.py
git commit -m "feat: 对话日志Repository实现"
```

---

### Task 4: Service

**Files:**
- Create: `src/modules/conversation/service.py`
- Test: `test/test_conversation.py`

**Interfaces:**
- Consumes: Task 1 `Conversation`/`ConversationTurn`；Task 2 全部 schema；Task 3 `ConversationRepository`/`ConversationTurnRepository`；`src.core.base_schema.PageResult`、`src.core.deps.PageParams`、`src.core.exceptions.BizException`；`src.modules.user.model.User`。
- Produces:
  - `class ConversationService`：`__init__(self, db: AsyncSession)`。
  - `async def list_conversations(self, params: PageParams, filters: ConversationFilter) -> PageResult[ConversationRead]`
  - `async def get_conversation(self, conversation_id: int) -> ConversationDetailRead`（不存在抛 `46001`）
  - `async def get_turns(self, conversation_id: int) -> list[ConversationTurnRead]`（对话不存在抛 `46001`）
  - `async def get_trace(self, turn_id: int) -> dict | None`（轮次不存在抛 `46002`，返回 `turn.trace`）
  - `async def annotate_conversation(self, conversation_id: int, data: ConversationAnnotateRequest, annotated_by: str) -> ConversationRead`（不存在抛 `46001`）
  - `async def export_conversation(self, conversation_id: int, format: str) -> tuple[str, str, str]`（返回 `(content, media_type, filename)`；不存在抛 `46001`；`format` 非法抛 `BizException(400, "不支持的导出格式")`）
  - 内部转换：`_to_read(self, conv: Conversation) -> ConversationRead`、`_to_turn_read(self, turn: ConversationTurn) -> ConversationTurnRead`。

- [ ] **Step 1: 写失败测试**

在 `test/test_conversation.py` 写 5 个测试（`@pytest.mark.asyncio` + `db_session`）：

```python
import pytest
from src.core.exceptions import BizException
from src.modules.conversation.service import ConversationService
from src.modules.conversation.schema import ConversationAnnotateRequest, ConversationFilter
from src.modules.conversation.model import Conversation, ConversationTurn

@pytest.mark.asyncio
async def test_get_conversation_not_found_raises(db_session):
    svc = ConversationService(db_session)
    with pytest.raises(BizException) as e:
        await svc.get_conversation(999)
    assert e.value.code == 46001

@pytest.mark.asyncio
async def test_annotate_builds_annotation(db_session):
    svc = ConversationService(db_session)
    await svc.repo.create(Conversation(agent_id="a1", agent_name="客服", user_id="u1",
        status="completed", turn_count=1, total_tokens=10, total_cost=0.1,
        total_duration=100, started_at=datetime(2024,2,7,10,0)))
    read = await svc.annotate_conversation(1, ConversationAnnotateRequest(rating=5, tags=["准确"], notes="ok"), "admin")
    assert read.id == 1

@pytest.mark.asyncio
async def test_export_json(db_session):
    svc = ConversationService(db_session)
    await svc.repo.create(Conversation(agent_id="a1", agent_name="客服", user_id="u1",
        status="completed", turn_count=1, total_tokens=10, total_cost=0.0234,
        total_duration=45, started_at=datetime(2024,2,7,10,0)))
    content, media_type, filename = await svc.export_conversation(1, "json")
    assert media_type == "application/json"
    assert "total_duration" in content

@pytest.mark.asyncio
async def test_export_invalid_format_raises(db_session):
    svc = ConversationService(db_session)
    with pytest.raises(BizException) as e:
        await svc.export_conversation(1, "pdf")
    assert e.value.code == 400

@pytest.mark.asyncio
async def test_get_trace_turn_not_found_raises(db_session):
    svc = ConversationService(db_session)
    with pytest.raises(BizException) as e:
        await svc.get_trace(999)
    assert e.value.code == 46002
```

（`test_annotate_builds_annotation` 中再通过 `(await svc.repo.get_by_id(1)).annotation` 断言键为 `rating/tags/notes/annotatedBy/annotatedAt`。）

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_conversation.py::test_get_conversation_not_found_raises -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'src.modules.conversation.service'`

- [ ] **Step 3: 实现 `src/modules/conversation/service.py`**

按 Produces 实现各方法。要点：
- `_to_read` 手工逐字段构造 `ConversationRead`（`total_cost` 用 `float(conv.total_cost)`，`started_at`/`ended_at` 原样）。
- `get_conversation` 查 `repo.get_by_id`，不存在抛 `46001`，再 `turn_repo.get_turns_by_conversation` 组装 `ConversationDetailRead`（`annotation` 取 `conv.annotation`）。
- `annotate_conversation` 构造 `annotation` dict（键 `rating/tags/notes/annotatedBy/annotatedAt`，`annotatedAt=datetime.now().isoformat()`），写回 `conv.annotation` 并 `repo.update`，返回 `_to_read`。
- `export_conversation`：先取详情；`format=="json"` → `content = json.dumps(detail.model_dump(mode="json"), ensure_ascii=False, indent=2)`、`media_type="application/json"`、`filename=f"conversation_{id}.json"`；`format=="txt"` → 拼接可读文本（含会话头与 `[序号] 用户/助手: content`），`media_type="text/plain"`、`filename=f"conversation_{id}.txt"`；其它 `format` 抛 `BizException(400, "不支持的导出格式")`。

- [ ] **Step 4: 运行确认通过**

Run: `pytest test/test_conversation.py -v`
Expected: PASS（本 Task 相关 5 个测试全绿）

- [ ] **Step 5: Commit**

```bash
git add src/modules/conversation/service.py test/test_conversation.py
git commit -m "feat: 对话日志Service实现"
```

---

### Task 5: API 路由 + main.py 注册

**Files:**
- Create: `src/modules/conversation/api.py`
- Modify: `src/main.py:11-21, 80-85`
- Test: `test/test_conversation.py`

**Interfaces:**
- Consumes: `src.modules.conversation.service.ConversationService`；`src.infra.database.get_db`；`src.core.deps.PageParams`、`src.core.deps.get_current_user`；`src.core.base_schema.ResponseSchema`、`PageResult`；`src.modules.user.model.User`。
- Produces:
  - `router = APIRouter(prefix="/conversations", tags=["对话日志"])`
  - `turn_router = APIRouter(prefix="/turns", tags=["对话日志"])`
  - `def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService`
  - 路由：
    - `GET ""` → `list_conversations(params: PageParams, filters: ConversationFilter)`，返回 `ResponseSchema[PageResult[ConversationRead]]`
    - `GET "/{conversation_id}"` → `ResponseSchema[ConversationDetailRead]`
    - `GET "/{conversation_id}/turns"` → `ResponseSchema[list[ConversationTurnRead]]`
    - `POST "/{conversation_id}/annotate"` → `ResponseSchema[ConversationRead]`
    - `GET "/{conversation_id}/export"` → `Response`（`content`/`media_type`/`Content-Disposition` 下载）
    - `GET "/{turn_id}/trace"`（`turn_router`）→ `ResponseSchema[dict | None]`
  - 每个路由签名末尾加 `_: User = Depends(get_current_user)`；annotate 额外取 `current_user: User = Depends(get_current_user)` 并传 `current_user.username`。

- [ ] **Step 1: 写失败测试**

在 `test/test_conversation.py` 写 `test_conversation_routes_registered` 与 `test_list_conversations_endpoint`：

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.modules.conversation.api import router, turn_router

def test_conversation_routes_registered():
    paths = {r.path for r in router.routes} | {r.path for r in turn_router.routes}
    assert "/conversations" in paths
    assert "/conversations/{conversation_id}" in paths
    assert "/conversations/{conversation_id}/turns" in paths
    assert "/conversations/{conversation_id}/annotate" in paths
    assert "/conversations/{conversation_id}/export" in paths
    assert "/turns/{turn_id}/trace" in paths
```

`test_list_conversations_endpoint`：建一个独立的 `FastAPI()` 并 `include_router(router, prefix="/api/v1")`、`include_router(turn_router, prefix="/api/v1")`，用 `app.dependency_overrides[get_db]` 指向 `db_session`、`app.dependency_overrides[get_current_user]` 指向返回假 `User` 的 stub，`TestClient(app).get("/api/v1/conversations")`，断言 `status_code == 200` 且 `resp.json()["code"] == 200`、`data` 含 `items`/`total`。

- [ ] **Step 2: 运行确认失败**

Run: `pytest test/test_conversation.py::test_conversation_routes_registered -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'src.modules.conversation.api'`

- [ ] **Step 3: 实现 `src/modules/conversation/api.py`**

按 Produces 定义 `router`/`turn_router`、`get_conversation_service` 与 6 个路由；`export` 用 `from fastapi import Response`，`Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})`。

- [ ] **Step 4: 在 `src/main.py` 注册路由**

追加 `from src.modules.conversation.api import router as conversation_router, turn_router`，并在路由注册区加 `app.include_router(conversation_router, prefix="/api/v1")`、`app.include_router(turn_router, prefix="/api/v1")`。

- [ ] **Step 5: 运行确认通过**

Run: `pytest test/test_conversation.py -v`
Expected: PASS（全部测试绿）

- [ ] **Step 6: 冒烟验证**

Run: `uvicorn src.main:app --port 8080 --reload` 后访问 `/docs`，确认出现「对话日志」标签下的 `/api/v1/conversations` 等 6 个接口；`GET /api/v1/conversations`（带 JWT）返回 `{"code":200,"data":{"items":[...],"total":0,...}}`。

- [ ] **Step 7: Commit**

```bash
git add src/modules/conversation/api.py src/main.py test/test_conversation.py
git commit -m "feat: 对话日志API路由注册"
```

---

## Self-Review 备注

- 覆盖：列表分页+筛选（agent_id/status/user_id/satisfaction/annotated/时间范围/keyword）、详情（turns+annotation）、轮次列表、链路追踪、标注、导出均落到 Task 3/4/5；无独立创建入口（与 Spec 一致）。
- 命名一致性：`ConversationFilter`/`ConversationRead`/`ConversationTurnRead`/`ConversationDetailRead`/`ConversationAnnotateRequest` 在 schema→repository→service→api 全程同名单签名；`router`/`turn_router` 在 api→main 同命。
- Review Focus 5 条均已绑定到对应 Task 的测试。
- 字段名与类型逐字对照 `types/conversation.ts`（见 Global Constraints 映射表）；`satisfaction` 为字符串枚举、`total_duration` 为毫秒 int、`total_cost` 为 float，均在测试中锁定。
