from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.approval.schema import (
    ApplicationRead,
    ApprovalApply,
    ApprovalAuditRequest,
)
from app.modules.approval.service import ApprovalService
from app.modules.user.model import User

router = APIRouter(prefix="/approvals", tags=["权限申请"])


def get_approval_service(db: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


@router.post(
    "/apply", response_model=ResponseSchema[ApplicationRead], summary="发起权限申请"
)
async def apply_permission(
    data: ApprovalApply,
    svc: ApprovalService = Depends(get_approval_service),
    current_user: User = Depends(get_current_user_with_permission("approval:apply")),
) -> ResponseSchema[ApplicationRead]:
    application = await svc.apply(current_user, data)
    return ResponseSchema(data=ApplicationRead.model_validate(application))


@router.get(
    "/my", response_model=ResponseSchema[PageResult[ApplicationRead]], summary="我的申请"
)
async def my_applications(
    params: PageParams = Depends(),
    svc: ApprovalService = Depends(get_approval_service),
    current_user: User = Depends(get_current_user_with_permission("approval:apply")),
) -> ResponseSchema[PageResult[ApplicationRead]]:
    rows, total = await svc.my(current_user, params)
    return ResponseSchema(
        data=PageResult(
            items=[ApplicationRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.get(
    "/list", response_model=ResponseSchema[PageResult[ApplicationRead]], summary="待审批列表"
)
async def list_applications(
    params: PageParams = Depends(),
    status: str | None = Query(None),
    svc: ApprovalService = Depends(get_approval_service),
    _: User = Depends(get_current_user_with_permission("approval:audit")),
) -> ResponseSchema[PageResult[ApplicationRead]]:
    rows, total = await svc.list_all(params, status)
    return ResponseSchema(
        data=PageResult(
            items=[ApplicationRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.put(
    "/{application_id}/audit",
    response_model=ResponseSchema[ApplicationRead],
    summary="审批权限申请",
)
async def audit_application(
    application_id: int,
    data: ApprovalAuditRequest,
    svc: ApprovalService = Depends(get_approval_service),
    current_user: User = Depends(get_current_user_with_permission("approval:audit")),
) -> ResponseSchema[ApplicationRead]:
    application = await svc.audit_application(current_user, application_id, data)
    return ResponseSchema(data=ApplicationRead.model_validate(application))
