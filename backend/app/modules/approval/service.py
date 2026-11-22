from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.approval.model import PermissionApplication
from app.modules.approval.repository import ApprovalRepository
from app.modules.approval.schema import ApprovalApply, ApprovalAuditRequest
from app.modules.audit.service import AuditService
from app.modules.permission.model import Permission
from app.modules.user.model import User


class ApprovalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ApprovalRepository(db)
        self.audit = AuditService(db)

    async def apply(self, actor: User, data: ApprovalApply) -> PermissionApplication:
        reason = data.reason.strip()
        if not reason:
            raise BizException(code=400, message="申请理由不能为空")

        exists = await self.db.scalar(
            select(Permission.id).where(Permission.code == data.permission_code)
        )
        if not exists:
            raise BizException(code=404, message="权限码不存在")
        if await self.repo.find_pending(actor.id, data.permission_code):
            raise BizException(code=400, message="该权限已提交申请，请等待审批")

        application = PermissionApplication(
            applicant_id=actor.id,
            applicant_name=actor.username,
            permission_code=data.permission_code,
            reason=reason,
            status="pending",
            expired_at=data.expired_at,
        )
        self.db.add(application)
        await self.db.flush()
        self.audit.record(
            actor,
            module="approval",
            action="apply",
            target_id=application.id,
            target_name=data.permission_code,
            detail={"permission_code": data.permission_code, "reason": reason},
        )
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def my(self, actor: User, params: PageParams) -> tuple[list[PermissionApplication], int]:
        return await self.repo.list_for_applicant(actor.id, params.offset, params.page_size)

    async def list_all(
        self, params: PageParams, status: str | None = None
    ) -> tuple[list[PermissionApplication], int]:
        conditions = [PermissionApplication.status == status] if status else []
        return await self.repo.get_page(
            params.offset,
            params.page_size,
            params.keyword,
            extra_conditions=conditions,
            order_desc=True,
        )

    async def audit_application(
        self, actor: User, application_id: int, data: ApprovalAuditRequest
    ) -> PermissionApplication:
        application = await self.repo.get_by_id(application_id)
        if not application:
            raise BizException(code=404, message="申请记录不存在")
        if application.status != "pending":
            raise BizException(code=400, message="该申请已处理，不能重复审批")

        now = datetime.now()
        if data.approved and data.expired_at and data.expired_at <= now:
            raise BizException(code=400, message="过期时间必须晚于当前时间")

        application.approver_id = actor.id
        application.approver_name = actor.username
        application.approved_at = now
        if data.approved:
            application.status = "approved"
            if data.expired_at is not None:
                application.expired_at = data.expired_at
        else:
            application.status = "rejected"

        self.audit.record(
            actor,
            module="approval",
            action="approve" if data.approved else "reject",
            target_id=application.id,
            target_name=application.permission_code,
            detail={
                "applicant": application.applicant_name,
                "approved": data.approved,
                "comment": data.comment,
                "expired_at": application.expired_at,
            },
        )
        await self.db.commit()
        await self.db.refresh(application)
        return application
