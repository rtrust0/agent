from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.system.model import Alert, AlertRule, ApiKey, SystemSetting


class ApiKeyRepository(BaseRepository[ApiKey]):
    SEARCH_FIELDS = ["name"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ApiKey, db)

    async def get_by_key(self, key: str) -> ApiKey | None:
        return await self.db.scalar(select(ApiKey).where(ApiKey.key == key))


class AlertRuleRepository(BaseRepository[AlertRule]):
    SEARCH_FIELDS = ["name", "description"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AlertRule, db)


class AlertRepository(BaseRepository[Alert]):
    SEARCH_FIELDS = ["title", "source"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Alert, db)

    async def list_active(self, limit: int = 100) -> list[Alert]:
        rows = await self.db.execute(
            select(Alert)
            .where(Alert.status == "active")
            .order_by(Alert.last_occurred_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())


class SystemSettingRepository(BaseRepository[SystemSetting]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(SystemSetting, db)

    async def get_singleton(self) -> SystemSetting | None:
        return await self.db.scalar(select(SystemSetting).order_by(SystemSetting.id.asc()))
