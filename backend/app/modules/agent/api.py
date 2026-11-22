from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.agent.schema import (
    AgentCreate,
    AgentMonitorRead,
    AgentPublishRequest,
    AgentRead,
    AgentTestRequest,
    AgentTestResult,
    AgentUpdate,
    AgentVersionRead,
)
from app.modules.agent.service import AgentService
from app.modules.user.model import User

router = APIRouter(prefix="/agents", tags=["Agent 管理"])


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(db)


@router.get("", response_model=ResponseSchema[PageResult[AgentRead]], summary="Agent 列表")
async def list_agents(
    params: PageParams = Depends(),
    status: str | None = Query(None),
    type: str | None = Query(None),
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:list")),
) -> ResponseSchema[PageResult[AgentRead]]:
    agents, total = await svc.list_agents(params, current_user, status=status, type_=type)
    return ResponseSchema(
        data=PageResult(
            items=[AgentRead.model_validate(a) for a in agents],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[AgentRead], summary="创建 Agent")
async def create_agent(
    data: AgentCreate,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:create")),
) -> ResponseSchema[AgentRead]:
    agent = await svc.create(current_user, data)
    return ResponseSchema(data=AgentRead.model_validate(agent))


@router.get("/{agent_id}", response_model=ResponseSchema[AgentRead], summary="Agent 详情")
async def get_agent(
    agent_id: int,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:read")),
) -> ResponseSchema[AgentRead]:
    agent = await svc.get_agent(agent_id, current_user)
    return ResponseSchema(data=AgentRead.model_validate(agent))


@router.put("/{agent_id}", response_model=ResponseSchema[AgentRead], summary="更新 Agent")
async def update_agent(
    agent_id: int,
    data: AgentUpdate,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:update")),
) -> ResponseSchema[AgentRead]:
    agent = await svc.update(current_user, agent_id, data)
    return ResponseSchema(data=AgentRead.model_validate(agent))


@router.delete("/{agent_id}", response_model=ResponseSchema[None], summary="删除 Agent")
async def delete_agent(
    agent_id: int,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:delete")),
) -> ResponseSchema[None]:
    await svc.delete(current_user, agent_id)
    return ResponseSchema(data=None)


@router.post(
    "/{agent_id}/publish", response_model=ResponseSchema[AgentRead], summary="发布 / 下线 Agent"
)
async def publish_agent(
    agent_id: int,
    data: AgentPublishRequest | None = None,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:publish")),
) -> ResponseSchema[AgentRead]:
    agent = await svc.publish(current_user, agent_id, data.changelog if data else None)
    return ResponseSchema(data=AgentRead.model_validate(agent))


@router.get(
    "/{agent_id}/versions",
    response_model=ResponseSchema[list[AgentVersionRead]],
    summary="Agent 版本列表",
)
async def list_agent_versions(
    agent_id: int,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:read")),
) -> ResponseSchema[list[AgentVersionRead]]:
    versions = await svc.list_versions(agent_id, current_user)
    return ResponseSchema(data=[AgentVersionRead.model_validate(v) for v in versions])


@router.post(
    "/{agent_id}/versions/{version}/rollback",
    response_model=ResponseSchema[AgentRead],
    summary="回滚 Agent 版本",
)
async def rollback_agent(
    agent_id: int,
    version: str,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:publish")),
) -> ResponseSchema[AgentRead]:
    agent = await svc.rollback(current_user, agent_id, version)
    return ResponseSchema(data=AgentRead.model_validate(agent))


@router.post(
    "/{agent_id}/test", response_model=ResponseSchema[AgentTestResult], summary="Agent 调试测试"
)
async def test_agent(
    agent_id: int,
    data: AgentTestRequest,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:test")),
) -> ResponseSchema[AgentTestResult]:
    result = await svc.test(current_user, agent_id, data.input)
    return ResponseSchema(data=result)


@router.get(
    "/{agent_id}/monitor",
    response_model=ResponseSchema[AgentMonitorRead],
    summary="Agent 监控",
)
async def monitor_agent(
    agent_id: int,
    svc: AgentService = Depends(get_agent_service),
    current_user: User = Depends(get_current_user_with_permission("agent:monitor")),
) -> ResponseSchema[AgentMonitorRead]:
    data = await svc.monitor(agent_id, current_user)
    return ResponseSchema(data=data)
