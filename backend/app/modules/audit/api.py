from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.audit.schema import AuditLogRead
from app.modules.audit.service import AuditService
from app.modules.user.model import User

router = APIRouter(prefix="/system", tags=["审计日志"])


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get(
    "/audit-logs",
    response_model=ResponseSchema[PageResult[AuditLogRead]],
    summary="审计日志分页查询",
)
async def list_audit_logs(
    params: PageParams = Depends(),
    module: str | None = Query(None),
    action: str | None = Query(None),
    username: str | None = Query(None),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    svc: AuditService = Depends(get_audit_service),
    _: User = Depends(get_current_user_with_permission("system:audit")),
) -> ResponseSchema[PageResult[AuditLogRead]]:
    rows, total = await svc.search_page(
        params.offset,
        params.page_size,
        module=module,
        action=action,
        username=username,
        start_at=start_at,
        end_at=end_at,
    )
    return ResponseSchema(
        data=PageResult(
            items=[AuditLogRead.model_validate(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.get("/audit-logs/export", summary="审计日志导出（CSV）")
async def export_audit_logs(
    module: str | None = Query(None),
    action: str | None = Query(None),
    username: str | None = Query(None),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    svc: AuditService = Depends(get_audit_service),
    _: User = Depends(get_current_user_with_permission("system:audit")),
) -> Response:
    content = await svc.export_csv(
        module=module,
        action=action,
        username=username,
        start_at=start_at,
        end_at=end_at,
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-logs.csv"'},
    )
