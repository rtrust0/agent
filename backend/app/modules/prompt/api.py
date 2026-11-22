from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.prompt.schema import (
    PromptCreate,
    PromptPublishRequest,
    PromptRead,
    PromptTestRequest,
    PromptTestResult,
    PromptUpdate,
    PromptVersionRead,
)
from app.modules.prompt.service import PromptService
from app.modules.user.model import User

router = APIRouter(prefix="/prompts", tags=["Prompt 管理"])


def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    return PromptService(db)


@router.get("", response_model=ResponseSchema[PageResult[PromptRead]], summary="Prompt 列表")
async def list_prompts(
    params: PageParams = Depends(),
    category: str | None = Query(None),
    status: str | None = Query(None),
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:list")),
) -> ResponseSchema[PageResult[PromptRead]]:
    prompts, total = await svc.list_prompts(
        params, current_user, category=category, status=status
    )
    return ResponseSchema(
        data=PageResult(
            items=[PromptRead.model_validate(p) for p in prompts],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[PromptRead], summary="创建 Prompt")
async def create_prompt(
    data: PromptCreate,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:create")),
) -> ResponseSchema[PromptRead]:
    prompt = await svc.create(current_user, data)
    return ResponseSchema(data=PromptRead.model_validate(prompt))


@router.get("/{prompt_id}", response_model=ResponseSchema[PromptRead], summary="Prompt 详情")
async def get_prompt(
    prompt_id: int,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:read")),
) -> ResponseSchema[PromptRead]:
    prompt = await svc.get_prompt(prompt_id, current_user)
    return ResponseSchema(data=PromptRead.model_validate(prompt))


@router.put("/{prompt_id}", response_model=ResponseSchema[PromptRead], summary="更新 Prompt")
async def update_prompt(
    prompt_id: int,
    data: PromptUpdate,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:update")),
) -> ResponseSchema[PromptRead]:
    prompt = await svc.update(current_user, prompt_id, data)
    return ResponseSchema(data=PromptRead.model_validate(prompt))


@router.delete("/{prompt_id}", response_model=ResponseSchema[None], summary="删除 Prompt")
async def delete_prompt(
    prompt_id: int,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:delete")),
) -> ResponseSchema[None]:
    await svc.delete(current_user, prompt_id)
    return ResponseSchema(data=None)


@router.post(
    "/{prompt_id}/publish",
    response_model=ResponseSchema[PromptRead],
    summary="发布 Prompt 版本",
)
async def publish_prompt(
    prompt_id: int,
    data: PromptPublishRequest | None = None,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:publish")),
) -> ResponseSchema[PromptRead]:
    prompt = await svc.publish(current_user, prompt_id, data.changelog if data else None)
    return ResponseSchema(data=PromptRead.model_validate(prompt))


@router.get(
    "/{prompt_id}/versions",
    response_model=ResponseSchema[list[PromptVersionRead]],
    summary="Prompt 版本列表",
)
async def list_prompt_versions(
    prompt_id: int,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:read")),
) -> ResponseSchema[list[PromptVersionRead]]:
    versions = await svc.list_versions(prompt_id, current_user)
    return ResponseSchema(data=[PromptVersionRead.model_validate(v) for v in versions])


@router.post(
    "/{prompt_id}/versions/{version}/rollback",
    response_model=ResponseSchema[PromptRead],
    summary="回滚 Prompt 版本",
)
async def rollback_prompt(
    prompt_id: int,
    version: str,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:publish")),
) -> ResponseSchema[PromptRead]:
    prompt = await svc.rollback(current_user, prompt_id, version)
    return ResponseSchema(data=PromptRead.model_validate(prompt))


@router.post(
    "/{prompt_id}/test",
    response_model=ResponseSchema[PromptTestResult],
    summary="Prompt 调试测试",
)
async def test_prompt(
    prompt_id: int,
    data: PromptTestRequest,
    svc: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user_with_permission("prompt:test")),
) -> ResponseSchema[PromptTestResult]:
    result = await svc.test(current_user, prompt_id, data.variables)
    return ResponseSchema(data=result)
