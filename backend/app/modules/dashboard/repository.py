from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.model import Agent
from app.modules.conversation.model import Conversation
from app.modules.knowledge.model import Document, KnowledgeBase, Segment
from app.modules.model.model import LLMModel
from app.modules.permission.model import Permission
from app.modules.role.model import Role
from app.modules.system.model import Alert
from app.modules.tool.model import Tool
from app.modules.user.model import User


class DashboardRepository:
    """工作台聚合查询。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count(self, model, *conditions) -> int:
        stmt = select(func.count()).select_from(model)
        if conditions:
            stmt = stmt.where(*conditions)
        return (await self.db.execute(stmt)).scalar_one()

    async def today_conversations(self) -> int:
        start = datetime.combine(datetime.now().date(), datetime.min.time())
        return await self.count(Conversation, Conversation.started_at >= start)

    async def trend(self, days: int = 7) -> dict[str, tuple[int, int, float]]:
        start = datetime.now() - timedelta(days=days - 1)
        rows = await self.db.execute(
            select(
                func.date(Conversation.started_at),
                func.count(Conversation.id),
                func.coalesce(func.sum(Conversation.total_tokens), 0),
                func.coalesce(func.sum(Conversation.total_cost), 0),
            )
            .where(Conversation.started_at >= start)
            .group_by(func.date(Conversation.started_at))
        )
        return {
            str(day): (count, int(tokens), float(cost))
            for day, count, tokens, cost in rows.all()
        }

    async def top_agents(self, limit: int = 5) -> list[tuple[int, str, int, float]]:
        rows = await self.db.execute(
            select(
                Agent.id,
                Agent.name,
                func.count(Conversation.id),
                Agent.success_rate,
            )
            .outerjoin(Conversation, Conversation.agent_id == Agent.id)
            .group_by(Agent.id, Agent.name, Agent.success_rate)
            .order_by(func.count(Conversation.id).desc(), Agent.id.asc())
            .limit(limit)
        )
        return [(agent_id, name, count, float(rate)) for agent_id, name, count, rate in rows.all()]

    async def recent_alerts(self, limit: int = 5) -> list[Alert]:
        rows = await self.db.execute(
            select(Alert).order_by(Alert.last_occurred_at.desc()).limit(limit)
        )
        return list(rows.scalars().all())

    async def resource_usage(self, days: int = 7) -> dict[str, float]:
        document_count = await self.count(Document)
        segment_count = await self.count(Segment)
        storage_chars = (
            await self.db.execute(select(func.coalesce(func.sum(Segment.word_count), 0)))
        ).scalar_one()
        start = datetime.now() - timedelta(days=days)
        token_usage = (
            await self.db.execute(
                select(func.coalesce(func.sum(Conversation.total_tokens), 0)).where(
                    Conversation.started_at >= start
                )
            )
        ).scalar_one()
        api_calls = (
            await self.db.execute(select(func.coalesce(func.sum(Tool.call_count_7d), 0)))
        ).scalar_one()
        return {
            "storage_mb": round(float(storage_chars) / 1024 / 1024, 4),
            "document_count": float(document_count),
            "segment_count": float(segment_count),
            "token_usage_7d": float(token_usage),
            "api_calls_7d": float(api_calls),
        }

    async def basic_counts(self) -> dict[str, int]:
        return {
            "total_users": await self.count(User),
            "total_roles": await self.count(Role),
            "total_permissions": await self.count(Permission),
            "total_agents": await self.count(Agent),
            "active_agents": await self.count(Agent, Agent.status == "active"),
            "total_models": await self.count(LLMModel),
            "total_knowledge_bases": await self.count(KnowledgeBase),
            "total_tools": await self.count(Tool),
            "total_conversations": await self.count(Conversation),
        }
