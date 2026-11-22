from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import ResponseSchema
from app.core.database import get_db
from app.core.deps import get_current_user_with_permission
from app.modules.analytics.schema import (
    AgentMetric,
    AnalyticsOverview,
    CostSummary,
    DailyMetric,
    EvaluationSummary,
    ModelMetric,
)
from app.modules.analytics.service import AnalyticsService
from app.modules.user.model import User

router = APIRouter(prefix="/analytics", tags=["数据统计"])


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/overview", response_model=ResponseSchema[AnalyticsOverview], summary="总览")
async def get_overview(
    svc: AnalyticsService = Depends(get_analytics_service),
    _: User = Depends(get_current_user_with_permission("analytics:read")),
) -> ResponseSchema[AnalyticsOverview]:
    return ResponseSchema(data=await svc.overview())


@router.get("/daily", response_model=ResponseSchema[list[DailyMetric]], summary="按日统计")
async def get_daily(
    days: int = Query(14, ge=1, le=90),
    svc: AnalyticsService = Depends(get_analytics_service),
    _: User = Depends(get_current_user_with_permission("analytics:read")),
) -> ResponseSchema[list[DailyMetric]]:
    return ResponseSchema(data=await svc.daily(days))


@router.get("/by-agent", response_model=ResponseSchema[list[AgentMetric]], summary="按 Agent 统计")
async def get_by_agent(
    svc: AnalyticsService = Depends(get_analytics_service),
    _: User = Depends(get_current_user_with_permission("analytics:read")),
) -> ResponseSchema[list[AgentMetric]]:
    return ResponseSchema(data=await svc.by_agent())


@router.get("/by-model", response_model=ResponseSchema[list[ModelMetric]], summary="按模型统计")
async def get_by_model(
    svc: AnalyticsService = Depends(get_analytics_service),
    _: User = Depends(get_current_user_with_permission("analytics:read")),
) -> ResponseSchema[list[ModelMetric]]:
    return ResponseSchema(data=await svc.by_model())


@router.get("/costs", response_model=ResponseSchema[CostSummary], summary="费用统计")
async def get_costs(
    days: int = Query(14, ge=1, le=90),
    svc: AnalyticsService = Depends(get_analytics_service),
    _: User = Depends(get_current_user_with_permission("analytics:read")),
) -> ResponseSchema[CostSummary]:
    return ResponseSchema(data=await svc.costs(days))


@router.get(
    "/evaluation", response_model=ResponseSchema[EvaluationSummary], summary="效果评估"
)
async def get_evaluation(
    svc: AnalyticsService = Depends(get_analytics_service),
    _: User = Depends(get_current_user_with_permission("analytics:read")),
) -> ResponseSchema[EvaluationSummary]:
    return ResponseSchema(data=await svc.evaluation())
