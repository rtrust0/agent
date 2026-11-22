from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.role.model import Role


class RoleRepository(BaseRepository[Role]):
    SEARCH_FIELDS = ["code", "name"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Role, db)

    async def get_by_code(self, code: str) -> Role | None:
        return await self.db.scalar(select(Role).where(Role.code == code))
