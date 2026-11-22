from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.modules.approval.model import PermissionApplication


class ApprovalRepository(BaseRepository[PermissionApplication]):
    SEARCH_FIELDS = ["applicant_name", "permission_code"]

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(PermissionApplication, db)

    async def find_pending(self, applicant_id: int, permission_code: str) -> PermissionApplication | None:
        return await self.db.scalar(
            select(PermissionApplication).where(
                PermissionApplication.applicant_id == applicant_id,
                PermissionApplication.permission_code == permission_code,
                PermissionApplication.status == "pending",
            )
        )

    async def list_for_applicant(
        self, applicant_id: int, offset: int, limit: int
    ) -> tuple[list[PermissionApplication], int]:
        return await self.get_page(
            offset,
            limit,
            extra_conditions=[PermissionApplication.applicant_id == applicant_id],
            order_desc=True,
        )
