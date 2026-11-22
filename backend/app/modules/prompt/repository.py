from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.prompt.model import Prompt, PromptVersion


class PromptRepository(BaseRepository[Prompt]):
    SEARCH_FIELDS = ["name", "description", "category"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Prompt, db)


class PromptVersionRepository(BaseRepository[PromptVersion]):
    SEARCH_FIELDS = ["version", "changelog"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(PromptVersion, db)

    async def get_by_version(self, prompt_id: int, version: str) -> PromptVersion | None:
        return await self.db.scalar(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id, PromptVersion.version == version
            )
        )

    async def list_by_prompt(self, prompt_id: int) -> list[PromptVersion]:
        rows = await self.db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.id.desc())
        )
        return list(rows.scalars().all())

    async def clear_current(self, prompt_id: int) -> None:
        rows = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id, PromptVersion.is_current.is_(True)
            )
        )
        for row in rows.scalars().all():
            row.is_current = False
