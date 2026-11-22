from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schema import (
    AgentMetric,
    AnalyticsOverview,
    CostSummary,
    DailyMetric,
    EvaluationSummary,
    ModelMetric,
)
from app.modules.user.model import User


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)

    @staticmethod
    def _scope_user_id(current_user: User) -> int | None:
        """超管与 data_scope=all 不做过滤；own/dept 仅统计本人数据。"""
        if current_user.is_superuser or getattr(current_user, "data_scope", "own") == "all":
            return None
        return current_user.id

    async def overview(self, current_user: User) -> AnalyticsOverview:
        return AnalyticsOverview(**await self.repo.overview(self._scope_user_id(current_user)))

    async def daily(self, current_user: User, days: int = 14) -> list[DailyMetric]:
        raw = await self.repo.daily(days, self._scope_user_id(current_user))
        points: list[DailyMetric] = []
        today = date.today()
        for offset in range(days - 1, -1, -1):
            day = (today - timedelta(days=offset)).isoformat()
            conversations, tokens, cost = raw.get(day, (0, 0, 0.0))
            points.append(
                DailyMetric(
                    date=day,
                    conversations=conversations,
                    tokens=tokens,
                    cost=round(cost, 6),
                )
            )
        return points

    async def by_agent(self, current_user: User) -> list[AgentMetric]:
        names = await self.repo.agent_names()
        metrics: list[AgentMetric] = []
        for agent_id, agent_name, conversations, tokens, cost, avg_latency in (
            await self.repo.by_agent(self._scope_user_id(current_user))
        ):
            metrics.append(
                AgentMetric(
                    agent_id=agent_id,
                    agent_name=agent_name or names.get(agent_id, "未知 Agent"),
                    conversations=conversations,
                    tokens=int(tokens),
                    cost=round(float(cost), 6),
                    avg_latency_ms=int(avg_latency),
                )
            )
        return metrics

    async def by_model(self, current_user: User) -> list[ModelMetric]:
        metrics: list[ModelMetric] = []
        for model_id, model_name, conversations, tokens, cost in await self.repo.by_model(
            self._scope_user_id(current_user)
        ):
            metrics.append(
                ModelMetric(
                    model_id=model_id,
                    model_name=model_name or "未指定模型",
                    conversations=conversations,
                    tokens=int(tokens),
                    cost=round(float(cost), 6),
                )
            )
        return metrics

    async def costs(self, current_user: User, days: int = 14) -> CostSummary:
        overview = await self.repo.overview(self._scope_user_id(current_user))
        total = overview["total_cost"]
        conversations = overview["total_conversations"]
        return CostSummary(
            total_cost=round(total, 6),
            avg_cost_per_conversation=round(total / conversations, 6) if conversations else 0,
            daily=await self.daily(current_user, days),
        )

    async def evaluation(self, current_user: User) -> EvaluationSummary:
        return EvaluationSummary(**await self.repo.evaluation(self._scope_user_id(current_user)))
