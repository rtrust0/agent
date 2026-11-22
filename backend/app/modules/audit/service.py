import csv
import io
import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import client_ip, user_agent
from app.modules.audit.model import AuditLog
from app.modules.audit.repository import AuditLogRepository
from app.modules.user.model import User

CSV_HEADERS = [
    "id", "username", "action", "module", "target_id", "target_name", "detail", "ip_address", "created_at",
]


class AuditService:
    """审计日志：写入（Service 层调用）+ 查询 + 导出。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuditLogRepository(db)

    def record(
        self,
        actor: User | None,
        *,
        module: str,
        action: str,
        target_id: Any = None,
        target_name: str | None = None,
        detail: Any = None,
    ) -> AuditLog:
        """登记一条审计日志；由调用方统一 commit（与业务写入同事务）。"""
        log = AuditLog(
            user_id=getattr(actor, "id", None),
            username=getattr(actor, "username", "system"),
            action=action,
            module=module,
            target_id=None if target_id is None else str(target_id),
            target_name=target_name,
            detail=None if detail is None else json.dumps(detail, ensure_ascii=False, default=str),
            ip_address=client_ip(),
            user_agent=user_agent(),
        )
        self.db.add(log)
        return log

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
    ) -> tuple[list[AuditLog], int]:
        return await self.repo.search_page(
            offset,
            limit,
            module=module,
            action=action,
            username=username,
            start_at=start_at,
            end_at=end_at,
        )

    async def export_csv(
        self,
        *,
        module: str | None = None,
        action: str | None = None,
        username: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> str:
        rows = await self.repo.search_all(
            module=module,
            action=action,
            username=username,
            start_at=start_at,
            end_at=end_at,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_HEADERS)
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.username,
                    row.action,
                    row.module,
                    row.target_id or "",
                    row.target_name or "",
                    row.detail or "",
                    row.ip_address,
                    row.created_at.isoformat(sep=" ") if row.created_at else "",
                ]
            )
        return buffer.getvalue()
