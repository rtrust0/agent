from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user, get_current_user_with_permission
from app.modules.permission.schema import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)
from app.modules.permission.service import PermissionService
from app.modules.user.model import User

router = APIRouter(prefix="/permissions", tags=["权限"])


def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    return PermissionService(db)


@router.get("/", response_model=ResponseSchema[list[PermissionRead]], summary="权限全量列表")
async def list_permissions(
    svc: PermissionService = Depends(get_permission_service),
    _: User = Depends(get_current_user),
) -> ResponseSchema[list[PermissionRead]]:
    permissions = await svc.list_all()
    return ResponseSchema(data=[PermissionRead.model_validate(p) for p in permissions])


@router.get(
    "/search", response_model=ResponseSchema[PageResult[PermissionRead]], summary="分页搜索权限"
)
async def search_permissions(
    params: PageParams = Depends(),
    svc: PermissionService = Depends(get_permission_service),
    _: User = Depends(get_current_user_with_permission("permission:list")),
) -> ResponseSchema[PageResult[PermissionRead]]:
    permissions, total = await svc.search(params)
    return ResponseSchema(
        data=PageResult(
            items=[PermissionRead.model_validate(p) for p in permissions],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[PermissionRead], summary="创建权限")
async def create_permission(
    data: PermissionCreate,
    svc: PermissionService = Depends(get_permission_service),
    current_user: User = Depends(get_current_user_with_permission("permission:create")),
) -> ResponseSchema[PermissionRead]:
    permission = await svc.create(current_user, data)
    return ResponseSchema(data=PermissionRead.model_validate(permission))


@router.get("/{permission_id}", response_model=ResponseSchema[PermissionRead], summary="权限详情")
async def get_permission(
    permission_id: int,
    svc: PermissionService = Depends(get_permission_service),
    _: User = Depends(get_current_user_with_permission("permission:read")),
) -> ResponseSchema[PermissionRead]:
    permission = await svc.get_permission(permission_id)
    return ResponseSchema(data=PermissionRead.model_validate(permission))


@router.put("/{permission_id}", response_model=ResponseSchema[PermissionRead], summary="更新权限")
async def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    svc: PermissionService = Depends(get_permission_service),
    current_user: User = Depends(get_current_user_with_permission("permission:update")),
) -> ResponseSchema[PermissionRead]:
    permission = await svc.update(current_user, permission_id, data)
    return ResponseSchema(data=PermissionRead.model_validate(permission))


@router.delete("/{permission_id}", response_model=ResponseSchema[None], summary="删除权限")
async def delete_permission(
    permission_id: int,
    svc: PermissionService = Depends(get_permission_service),
    current_user: User = Depends(get_current_user_with_permission("permission:delete")),
) -> ResponseSchema[None]:
    await svc.delete(current_user, permission_id)
    return ResponseSchema(data=None)
