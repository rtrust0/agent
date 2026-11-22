from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.tool.model import Tool


class ToolRepository(BaseRepository[Tool]):
    SEARCH_FIELDS = ["name", "description"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Tool, db)

    async def get_by_name(self, name: str) -> Tool | None:
        return await self.db.scalar(select(Tool).where(Tool.name == name))
