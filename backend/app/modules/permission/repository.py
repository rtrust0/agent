from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.permission.model import Permission


class PermissionRepository(BaseRepository[Permission]):
    SEARCH_FIELDS = ["code", "name"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Permission, db)

    async def get_by_code(self, code: str) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.code == code))
