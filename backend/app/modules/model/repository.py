from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.model.model import LLMModel, ModelProvider


class ModelProviderRepository(BaseRepository[ModelProvider]):
    SEARCH_FIELDS = ["name", "type"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ModelProvider, db)


class LLMModelRepository(BaseRepository[LLMModel]):
    SEARCH_FIELDS = ["name", "model_id"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(LLMModel, db)

    async def get_by_model_id(self, model_id: str) -> LLMModel | None:
        return await self.db.scalar(select(LLMModel).where(LLMModel.model_id == model_id))

    async def clear_default(self, exclude_id: int | None = None) -> None:
        rows = await self.db.execute(select(LLMModel).where(LLMModel.is_default.is_(True)))
        for row in rows.scalars().all():
            if exclude_id is None or row.id != exclude_id:
                row.is_default = False
