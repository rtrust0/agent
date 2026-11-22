from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.tool.schema import (
    ToolCreate,
    ToolLogPage,
    ToolRead,
    ToolTestRequest,
    ToolTestResult,
    ToolUpdate,
)
from app.modules.tool.service import ToolService
from app.modules.user.model import User

router = APIRouter(prefix="/tools", tags=["工具管理"])


def get_tool_service(db: AsyncSession = Depends(get_db)) -> ToolService:
    return ToolService(db)


@router.get("", response_model=ResponseSchema[PageResult[ToolRead]], summary="工具列表")
async def list_tools(
    params: PageParams = Depends(),
    status: str | None = Query(None),
    type: str | None = Query(None),
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:list")),
) -> ResponseSchema[PageResult[ToolRead]]:
    tools, total = await svc.list_tools(params, current_user, status=status, type_=type)
    return ResponseSchema(
        data=PageResult(
            items=[ToolRead.model_validate(t) for t in tools],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[ToolRead], summary="注册工具")
async def create_tool(
    data: ToolCreate,
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:create")),
) -> ResponseSchema[ToolRead]:
    tool = await svc.create(current_user, data)
    return ResponseSchema(data=ToolRead.model_validate(tool))


@router.get("/{tool_id}", response_model=ResponseSchema[ToolRead], summary="工具详情")
async def get_tool(
    tool_id: int,
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:read")),
) -> ResponseSchema[ToolRead]:
    tool = await svc.get_tool(tool_id, current_user)
    return ResponseSchema(data=ToolRead.model_validate(tool))


@router.put("/{tool_id}", response_model=ResponseSchema[ToolRead], summary="更新工具")
async def update_tool(
    tool_id: int,
    data: ToolUpdate,
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:update")),
) -> ResponseSchema[ToolRead]:
    tool = await svc.update(current_user, tool_id, data)
    return ResponseSchema(data=ToolRead.model_validate(tool))


@router.delete("/{tool_id}", response_model=ResponseSchema[None], summary="删除工具")
async def delete_tool(
    tool_id: int,
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:delete")),
) -> ResponseSchema[None]:
    await svc.delete(current_user, tool_id)
    return ResponseSchema(data=None)


@router.post(
    "/{tool_id}/test", response_model=ResponseSchema[ToolTestResult], summary="工具测试"
)
async def test_tool(
    tool_id: int,
    data: ToolTestRequest | None = None,
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:test")),
) -> ResponseSchema[ToolTestResult]:
    result = await svc.test(current_user, tool_id, data.arguments if data else {})
    return ResponseSchema(data=result)


@router.post(
    "/{tool_id}/toggle", response_model=ResponseSchema[ToolRead], summary="启用/禁用工具"
)
async def toggle_tool(
    tool_id: int,
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:toggle")),
) -> ResponseSchema[ToolRead]:
    tool = await svc.toggle(current_user, tool_id)
    return ResponseSchema(data=ToolRead.model_validate(tool))


@router.get(
    "/{tool_id}/logs", response_model=ResponseSchema[ToolLogPage], summary="工具调用日志"
)
async def tool_logs(
    tool_id: int,
    params: PageParams = Depends(),
    svc: ToolService = Depends(get_tool_service),
    current_user: User = Depends(get_current_user_with_permission("tool:read")),
) -> ResponseSchema[ToolLogPage]:
    data = await svc.logs(tool_id, current_user, params)
    return ResponseSchema(data=data)
