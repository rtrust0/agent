from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.agent.model import Agent, AgentVersion


class AgentRepository(BaseRepository[Agent]):
    SEARCH_FIELDS = ["name", "description"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Agent, db)


class AgentVersionRepository(BaseRepository[AgentVersion]):
    SEARCH_FIELDS = ["version", "changelog"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentVersion, db)

    async def get_by_version(self, agent_id: int, version: str) -> AgentVersion | None:
        return await self.db.scalar(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id, AgentVersion.version == version)
            .order_by(AgentVersion.id.desc())
            .limit(1)
        )

    async def list_by_agent(self, agent_id: int) -> list[AgentVersion]:
        rows = await self.db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.id.desc())
        )
        return list(rows.scalars().all())

    async def clear_current(self, agent_id: int, exclude_id: int | None = None) -> None:
        rows = await self.db.execute(
            select(AgentVersion).where(
                AgentVersion.agent_id == agent_id, AgentVersion.is_current.is_(True)
            )
        )
        for row in rows.scalars().all():
            if exclude_id is None or row.id != exclude_id:
                row.is_current = False
