from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user_with_permission
from app.modules.model.schema import (
    ConnectionTestResult,
    ModelCreate,
    ModelRead,
    ModelUpdate,
    ProviderCreate,
    ProviderRead,
    ProviderUpdate,
)
from app.modules.model.service import ModelService
from app.modules.user.model import User

router = APIRouter(prefix="/models", tags=["模型管理"])


def get_model_service(db: AsyncSession = Depends(get_db)) -> ModelService:
    return ModelService(db)


# ---------------- 供应商 ----------------
@router.get(
    "/providers", response_model=ResponseSchema[list[ProviderRead]], summary="供应商列表"
)
async def list_providers(
    svc: ModelService = Depends(get_model_service),
    _: User = Depends(get_current_user_with_permission("model:provider_manage")),
) -> ResponseSchema[list[ProviderRead]]:
    providers = await svc.list_providers()
    return ResponseSchema(data=[ProviderRead.model_validate(p) for p in providers])


@router.post(
    "/providers", response_model=ResponseSchema[ProviderRead], summary="创建供应商"
)
async def create_provider(
    data: ProviderCreate,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:provider_manage")),
) -> ResponseSchema[ProviderRead]:
    provider = await svc.create_provider(current_user, data)
    return ResponseSchema(data=ProviderRead.model_validate(provider))


@router.get(
    "/providers/{provider_id}",
    response_model=ResponseSchema[ProviderRead],
    summary="供应商详情",
)
async def get_provider(
    provider_id: int,
    svc: ModelService = Depends(get_model_service),
    _: User = Depends(get_current_user_with_permission("model:provider_manage")),
) -> ResponseSchema[ProviderRead]:
    provider = await svc.get_provider(provider_id)
    return ResponseSchema(data=ProviderRead.model_validate(provider))


@router.put(
    "/providers/{provider_id}",
    response_model=ResponseSchema[ProviderRead],
    summary="更新供应商",
)
async def update_provider(
    provider_id: int,
    data: ProviderUpdate,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:provider_manage")),
) -> ResponseSchema[ProviderRead]:
    provider = await svc.update_provider(current_user, provider_id, data)
    return ResponseSchema(data=ProviderRead.model_validate(provider))


@router.delete(
    "/providers/{provider_id}", response_model=ResponseSchema[None], summary="删除供应商"
)
async def delete_provider(
    provider_id: int,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:provider_manage")),
) -> ResponseSchema[None]:
    await svc.delete_provider(current_user, provider_id)
    return ResponseSchema(data=None)


@router.post(
    "/providers/{provider_id}/test",
    response_model=ResponseSchema[ConnectionTestResult],
    summary="供应商连接测试",
)
async def test_provider(
    provider_id: int,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:test")),
) -> ResponseSchema[ConnectionTestResult]:
    result = await svc.test_provider(current_user, provider_id)
    return ResponseSchema(data=result)


# ---------------- 模型 ----------------
@router.get("", response_model=ResponseSchema[PageResult[ModelRead]], summary="模型列表")
async def list_models(
    params: PageParams = Depends(),
    provider_id: int | None = Query(None),
    status: str | None = Query(None),
    svc: ModelService = Depends(get_model_service),
    _: User = Depends(get_current_user_with_permission("model:list")),
) -> ResponseSchema[PageResult[ModelRead]]:
    models, total = await svc.list_models(params, provider_id=provider_id, status=status)
    return ResponseSchema(
        data=PageResult(
            items=[ModelRead.model_validate(m) for m in models],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[ModelRead], summary="创建模型")
async def create_model(
    data: ModelCreate,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:create")),
) -> ResponseSchema[ModelRead]:
    model = await svc.create_model(current_user, data)
    return ResponseSchema(data=ModelRead.model_validate(model))


@router.get("/{model_pk}", response_model=ResponseSchema[ModelRead], summary="模型详情")
async def get_model(
    model_pk: int,
    svc: ModelService = Depends(get_model_service),
    _: User = Depends(get_current_user_with_permission("model:read")),
) -> ResponseSchema[ModelRead]:
    model = await svc.get_model(model_pk)
    return ResponseSchema(data=ModelRead.model_validate(model))


@router.put("/{model_pk}", response_model=ResponseSchema[ModelRead], summary="更新模型")
async def update_model(
    model_pk: int,
    data: ModelUpdate,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:update")),
) -> ResponseSchema[ModelRead]:
    model = await svc.update_model(current_user, model_pk, data)
    return ResponseSchema(data=ModelRead.model_validate(model))


@router.delete("/{model_pk}", response_model=ResponseSchema[None], summary="删除模型")
async def delete_model(
    model_pk: int,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:delete")),
) -> ResponseSchema[None]:
    await svc.delete_model(current_user, model_pk)
    return ResponseSchema(data=None)


@router.post(
    "/{model_pk}/test",
    response_model=ResponseSchema[ConnectionTestResult],
    summary="模型连接测试",
)
async def test_model(
    model_pk: int,
    svc: ModelService = Depends(get_model_service),
    current_user: User = Depends(get_current_user_with_permission("model:test")),
) -> ResponseSchema[ConnectionTestResult]:
    result = await svc.test_model(current_user, model_pk)
    return ResponseSchema(data=result)
