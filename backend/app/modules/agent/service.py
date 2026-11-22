from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import assert_in_scope, scope_condition
from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.core.versioning import next_version
from app.modules.agent.model import Agent, AgentVersion
from app.modules.agent.repository import AgentRepository, AgentVersionRepository
from app.modules.agent.schema import AgentCreate, AgentMonitorRead, AgentTestResult, AgentUpdate
from app.modules.audit.service import AuditService
from app.modules.model.model import LLMModel
from app.modules.user.model import User


class AgentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AgentRepository(db)
        self.version_repo = AgentVersionRepository(db)
        self.audit = AuditService(db)

    async def list_agents(
        self,
        params: PageParams,
        current_user: User,
        *,
        status: str | None = None,
        type_: str | None = None,
    ) -> tuple[list[Agent], int]:
        conditions = []
        scope = scope_condition(Agent, current_user)
        if scope is not None:
            conditions.append(scope)
        if status:
            conditions.append(Agent.status == status)
        if type_:
            conditions.append(Agent.type == type_)
        return await self.repo.get_page(
            params.offset, params.page_size, params.keyword, extra_conditions=conditions or None
        )

    async def get_agent(self, agent_id: int, current_user: User) -> Agent:
        agent = await self.repo.get_by_id(agent_id)
        if not agent:
            raise BizException(code=404, message="Agent 不存在")
        assert_in_scope(agent, current_user, message="没有权限访问该 Agent")
        return agent

    async def create(self, actor: User, data: AgentCreate) -> Agent:
        await self._validate(data.type, data.model_id)
        agent = Agent(
            name=data.name.strip(),
            description=data.description,
            type=data.type,
            status="draft",
            model_id=data.model_id,
            config=data.config,
            version="v0.1",
            created_by=actor.username,
        )
        self.db.add(agent)
        await self.db.flush()
        self.audit.record(
            actor,
            module="agent",
            action="create",
            target_id=agent.id,
            target_name=agent.name,
            detail={"type": agent.type, "model_id": agent.model_id},
        )
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def update(self, actor: User, agent_id: int, data: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id, actor)
        await self._validate(data.type, data.model_id)
        if data.status is not None and data.status not in {"draft", "inactive", "error"}:
            raise BizException(code=400, message="请使用发布接口激活 Agent")
        before = {"name": agent.name, "status": agent.status, "model_id": agent.model_id}
        for field in ("name", "description", "type", "model_id", "config", "status"):
            value = getattr(data, field)
            if value is not None:
                setattr(agent, field, value)
        self.audit.record(
            actor,
            module="agent",
            action="update",
            target_id=agent.id,
            target_name=agent.name,
            detail={
                "before": before,
                "after": {"name": agent.name, "status": agent.status, "model_id": agent.model_id},
            },
        )
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def delete(self, actor: User, agent_id: int) -> None:
        agent = await self.get_agent(agent_id, actor)
        self.audit.record(
            actor, module="agent", action="delete", target_id=agent.id, target_name=agent.name
        )
        await self.repo.delete(agent)
        await self.db.commit()

    async def publish(self, actor: User, agent_id: int, changelog: str | None) -> Agent:
        agent = await self.get_agent(agent_id, actor)
        history = await self.version_repo.list_by_agent(agent.id)
        new_version = next_version(
            [item.version for item in history] + [agent.version], agent.version
        )
        await self.version_repo.clear_current(agent.id)
        version = AgentVersion(
            agent_id=agent.id,
            version=new_version,
            config=agent.config,
            changelog=changelog or "发布新版本",
            is_current=True,
            published_by=actor.username,
            published_at=datetime.now(),
        )
        self.db.add(version)
        agent.version = new_version
        agent.status = "active"
        self.audit.record(
            actor,
            module="agent",
            action="publish",
            target_id=agent.id,
            target_name=agent.name,
            detail={"version": new_version, "changelog": changelog},
        )
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def list_versions(self, agent_id: int, current_user: User) -> list[AgentVersion]:
        agent = await self.get_agent(agent_id, current_user)
        return await self.version_repo.list_by_agent(agent.id)

    async def rollback(self, actor: User, agent_id: int, version_name: str) -> Agent:
        agent = await self.get_agent(agent_id, actor)
        version = await self.version_repo.get_by_version(agent.id, version_name)
        if not version:
            raise BizException(code=404, message="目标版本不存在")
        await self.version_repo.clear_current(agent.id)
        version.is_current = True
        agent.version = version.version
        agent.config = version.config
        agent.status = "active"
        self.audit.record(
            actor,
            module="agent",
            action="rollback",
            target_id=agent.id,
            target_name=agent.name,
            detail={"version": version.version},
        )
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def test(self, actor: User, agent_id: int, user_input: str) -> AgentTestResult:
        agent = await self.get_agent(agent_id, actor)
        success = agent.status != "error"
        output = (
            f"[{agent.name}] 已收到输入：{user_input}" if success else "Agent 当前状态异常，请检查配置"
        )
        self.audit.record(
            actor,
            module="agent",
            action="test",
            target_id=agent.id,
            target_name=agent.name,
            detail={"success": success, "input_length": len(user_input)},
        )
        await self.db.commit()
        return AgentTestResult(
            agent_id=agent.id, success=success, output=output, latency_ms=1 if success else 0
        )

    async def monitor(self, agent_id: int, current_user: User) -> AgentMonitorRead:
        agent = await self.get_agent(agent_id, current_user)
        return AgentMonitorRead(
            agent_id=agent.id,
            name=agent.name,
            status=agent.status,
            call_count_7d=agent.call_count_7d,
            success_rate=float(agent.success_rate),
            avg_latency_ms=1200 if agent.call_count_7d else 0,
            version=agent.version,
            recent_errors=[] if agent.status != "error" else ["最近一次调用失败"],
        )

    async def _validate(self, type_: str | None, model_id: int | None) -> None:
        if type_ is not None and type_ not in {
            "conversation",
            "tool",
            "analysis",
            "creative",
            "workflow",
        }:
            raise BizException(code=400, message="Agent 类型不合法")
        if model_id is not None and not await self.db.get(LLMModel, model_id):
            raise BizException(code=404, message="模型不存在")
