from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import ResponseSchema
from app.core.database import get_db
from app.core.deps import get_current_user_with_permission
from app.modules.dashboard.schema import (
    AlertBrief,
    DashboardStats,
    ResourceUsage,
    TopAgent,
    TrendPoint,
)
from app.modules.dashboard.service import DashboardService
from app.modules.user.model import User

router = APIRouter(prefix="/dashboard", tags=["工作台"])


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("/stats", response_model=ResponseSchema[DashboardStats], summary="工作台统计")
async def get_stats(
    svc: DashboardService = Depends(get_dashboard_service),
    _: User = Depends(get_current_user_with_permission("dashboard:read")),
) -> ResponseSchema[DashboardStats]:
    return ResponseSchema(data=await svc.stats())


@router.get("/trends", response_model=ResponseSchema[list[TrendPoint]], summary="对话趋势")
async def get_trends(
    days: int = Query(7, ge=1, le=90),
    svc: DashboardService = Depends(get_dashboard_service),
    _: User = Depends(get_current_user_with_permission("dashboard:read")),
) -> ResponseSchema[list[TrendPoint]]:
    return ResponseSchema(data=await svc.trends(days))


@router.get(
    "/top-agents", response_model=ResponseSchema[list[TopAgent]], summary="Agent 调用排行"
)
async def get_top_agents(
    limit: int = Query(5, ge=1, le=20),
    svc: DashboardService = Depends(get_dashboard_service),
    _: User = Depends(get_current_user_with_permission("dashboard:read")),
) -> ResponseSchema[list[TopAgent]]:
    return ResponseSchema(data=await svc.top_agents(limit))


@router.get(
    "/recent-alerts",
    response_model=ResponseSchema[list[AlertBrief]],
    summary="最近告警",
)
async def get_recent_alerts(
    limit: int = Query(5, ge=1, le=20),
    svc: DashboardService = Depends(get_dashboard_service),
    _: User = Depends(get_current_user_with_permission("dashboard:read")),
) -> ResponseSchema[list[AlertBrief]]:
    return ResponseSchema(data=await svc.recent_alerts(limit))


@router.get(
    "/resource-usage",
    response_model=ResponseSchema[ResourceUsage],
    summary="资源用量",
)
async def get_resource_usage(
    svc: DashboardService = Depends(get_dashboard_service),
    _: User = Depends(get_current_user_with_permission("dashboard:read")),
) -> ResponseSchema[ResourceUsage]:
    return ResponseSchema(data=await svc.resource_usage())
