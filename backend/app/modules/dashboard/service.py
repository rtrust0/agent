from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schema import (
    AlertBrief,
    DashboardStats,
    ResourceUsage,
    TopAgent,
    TrendPoint,
)


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = DashboardRepository(db)

    async def stats(self) -> DashboardStats:
        counts = await self.repo.basic_counts()
        counts["today_conversations"] = await self.repo.today_conversations()
        return DashboardStats(**counts)

    async def trends(self, days: int = 7) -> list[TrendPoint]:
        raw = await self.repo.trend(days)
        points: list[TrendPoint] = []
        today = date.today()
        for offset in range(days - 1, -1, -1):
            day = (today - timedelta(days=offset)).isoformat()
            conversations, tokens, cost = raw.get(day, (0, 0, 0.0))
            points.append(
                TrendPoint(
                    date=day,
                    conversations=conversations,
                    tokens=tokens,
                    cost=round(cost, 6),
                )
            )
        return points

    async def top_agents(self, limit: int = 5) -> list[TopAgent]:
        rows = await self.repo.top_agents(limit)
        return [
            TopAgent(
                agent_id=agent_id,
                name=name,
                conversation_count=count,
                success_rate=rate,
            )
            for agent_id, name, count, rate in rows
        ]

    async def recent_alerts(self, limit: int = 5) -> list[AlertBrief]:
        alerts = await self.repo.recent_alerts(limit)
        return [AlertBrief.model_validate(alert) for alert in alerts]

    async def resource_usage(self) -> ResourceUsage:
        usage = await self.repo.resource_usage()
        return ResourceUsage(
            storage_mb=usage["storage_mb"],
            document_count=int(usage["document_count"]),
            segment_count=int(usage["segment_count"]),
            token_usage_7d=int(usage["token_usage_7d"]),
            api_calls_7d=int(usage["api_calls_7d"]),
        )
