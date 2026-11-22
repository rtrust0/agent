from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.audit.model import AuditLog


class AuditLogRepository(BaseRepository[AuditLog]):
    SEARCH_FIELDS = ["username", "target_name"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AuditLog, db)

    def _build_conditions(
        self,
        module: str | None,
        action: str | None,
        username: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> list:
        conditions = []
        if module:
            conditions.append(AuditLog.module == module)
        if action:
            conditions.append(AuditLog.action == action)
        if username:
            conditions.append(AuditLog.username.like(f"%{username}%"))
        if start_at:
            conditions.append(AuditLog.created_at >= start_at)
        if end_at:
            conditions.append(AuditLog.created_at <= end_at)
        return conditions

    async def search_page(
        self,
        offset: int,
        limit: int,
        *,
        module: str | None = None,
        action: str | None = None,
        username: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        order_desc: bool = True,
    ) -> tuple[list[AuditLog], int]:
        conditions = self._build_conditions(module, action, username, start_at, end_at)
        return await self.get_page(
            offset,
            limit,
            extra_conditions=conditions,
            order_desc=order_desc,
        )

    async def search_all(
        self,
        *,
        module: str | None = None,
        action: str | None = None,
        username: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        max_rows: int = 1000,
    ) -> list[AuditLog]:
        conditions = self._build_conditions(module, action, username, start_at, end_at)
        stmt = select(AuditLog)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(AuditLog.id.desc()).limit(max_rows)
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_by_action(self) -> dict[str, int]:
        rows = await self.db.execute(
            select(AuditLog.action, func.count()).group_by(AuditLog.action)
        )
        return {action: total for action, total in rows.all()}
