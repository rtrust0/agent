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


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)

    async def overview(self) -> AnalyticsOverview:
        return AnalyticsOverview(**await self.repo.overview())

    async def daily(self, days: int = 14) -> list[DailyMetric]:
        raw = await self.repo.daily(days)
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

    async def by_agent(self) -> list[AgentMetric]:
        names = await self.repo.agent_names()
        metrics: list[AgentMetric] = []
        for agent_id, agent_name, conversations, tokens, cost, avg_latency in (
            await self.repo.by_agent()
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

    async def by_model(self) -> list[ModelMetric]:
        metrics: list[ModelMetric] = []
        for model_id, model_name, conversations, tokens, cost in await self.repo.by_model():
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

    async def costs(self, days: int = 14) -> CostSummary:
        overview = await self.repo.overview()
        total = overview["total_cost"]
        conversations = overview["total_conversations"]
        return CostSummary(
            total_cost=round(total, 6),
            avg_cost_per_conversation=round(total / conversations, 6) if conversations else 0,
            daily=await self.daily(days),
        )

    async def evaluation(self) -> EvaluationSummary:
        return EvaluationSummary(**await self.repo.evaluation())
