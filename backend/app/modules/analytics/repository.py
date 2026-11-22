from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.model import Agent
from app.modules.conversation.model import Conversation
from app.modules.model.model import LLMModel


class AnalyticsRepository:
    """数据统计聚合查询（全部基于 conversations，支持按数据范围过滤）。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _scope(user_id: int | None) -> list:
        return [] if user_id is None else [Conversation.user_id == user_id]

    async def overview(self, user_id: int | None = None) -> dict:
        row = (
            await self.db.execute(
                select(
                    func.count(Conversation.id),
                    func.coalesce(func.sum(Conversation.total_tokens), 0),
                    func.coalesce(func.sum(Conversation.total_cost), 0),
                    func.coalesce(func.avg(Conversation.latency_ms), 0),
                ).where(*self._scope(user_id))
            )
        ).one()
        total, tokens, cost, avg_latency = row
        completed = (
            await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.status == "completed", *self._scope(user_id)
                )
            )
        ).scalar_one()
        errors = (
            await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.status == "error", *self._scope(user_id)
                )
            )
        ).scalar_one()
        return {
            "total_conversations": total,
            "completed_conversations": completed,
            "error_conversations": errors,
            "total_tokens": int(tokens),
            "total_cost": float(cost),
            "avg_latency_ms": int(avg_latency),
            "success_rate": round(completed / total * 100, 2) if total else 0.0,
        }

    async def daily(
        self, days: int, user_id: int | None = None
    ) -> dict[str, tuple[int, int, float]]:
        start = datetime.now() - timedelta(days=days - 1)
        rows = await self.db.execute(
            select(
                func.date(Conversation.started_at),
                func.count(Conversation.id),
                func.coalesce(func.sum(Conversation.total_tokens), 0),
                func.coalesce(func.sum(Conversation.total_cost), 0),
            )
            .where(Conversation.started_at >= start, *self._scope(user_id))
            .group_by(func.date(Conversation.started_at))
        )
        return {
            str(day): (count, int(tokens), float(cost))
            for day, count, tokens, cost in rows.all()
        }

    async def by_agent(self, user_id: int | None = None) -> list[tuple]:
        rows = await self.db.execute(
            select(
                Conversation.agent_id,
                Conversation.agent_name,
                func.count(Conversation.id),
                func.coalesce(func.sum(Conversation.total_tokens), 0),
                func.coalesce(func.sum(Conversation.total_cost), 0),
                func.coalesce(func.avg(Conversation.latency_ms), 0),
            )
            .where(*self._scope(user_id))
            .group_by(Conversation.agent_id, Conversation.agent_name)
            .order_by(func.count(Conversation.id).desc())
        )
        return list(rows.all())

    async def by_model(self, user_id: int | None = None) -> list[tuple]:
        rows = await self.db.execute(
            select(
                Conversation.model_id,
                LLMModel.name,
                func.count(Conversation.id),
                func.coalesce(func.sum(Conversation.total_tokens), 0),
                func.coalesce(func.sum(Conversation.total_cost), 0),
            )
            .select_from(Conversation)
            .outerjoin(LLMModel, LLMModel.id == Conversation.model_id)
            .where(*self._scope(user_id))
            .group_by(Conversation.model_id, LLMModel.name)
            .order_by(func.count(Conversation.id).desc())
        )
        return list(rows.all())

    async def evaluation(self, user_id: int | None = None) -> dict:
        positive = (
            await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.satisfaction == "positive", *self._scope(user_id)
                )
            )
        ).scalar_one()
        negative = (
            await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.satisfaction == "negative", *self._scope(user_id)
                )
            )
        ).scalar_one()
        avg_rating = (
            await self.db.execute(
                select(func.coalesce(func.avg(Conversation.rating), 0)).where(
                    *self._scope(user_id)
                )
            )
        ).scalar_one()
        needs_optimization = (
            await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.needs_optimization.is_(True), *self._scope(user_id)
                )
            )
        ).scalar_one()
        rated = positive + negative
        return {
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": round(positive / rated * 100, 2) if rated else 0.0,
            "avg_rating": round(float(avg_rating), 2),
            "needs_optimization": needs_optimization,
        }

    async def agent_names(self) -> dict[int, str]:
        rows = await self.db.execute(select(Agent.id, Agent.name))
        return {agent_id: name for agent_id, name in rows.all()}
