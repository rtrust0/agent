from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user, get_current_user_with_permission
from app.modules.role.schema import (
    RoleAssignPermissions,
    RoleCreate,
    RoleRead,
    RoleUpdate,
)
from app.modules.role.service import RoleService
from app.modules.user.model import User

router = APIRouter(prefix="/roles", tags=["角色"])


def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    return RoleService(db)


@router.get("/", response_model=ResponseSchema[list[RoleRead]], summary="角色全量列表")
async def list_roles(
    svc: RoleService = Depends(get_role_service),
    _: User = Depends(get_current_user),
) -> ResponseSchema[list[RoleRead]]:
    roles = await svc.list_all()
    return ResponseSchema(data=[RoleRead.model_validate(role) for role in roles])


@router.get("/search", response_model=ResponseSchema[PageResult[RoleRead]], summary="分页搜索角色")
async def search_roles(
    params: PageParams = Depends(),
    svc: RoleService = Depends(get_role_service),
    _: User = Depends(get_current_user_with_permission("role:list")),
) -> ResponseSchema[PageResult[RoleRead]]:
    roles, total = await svc.search(params)
    return ResponseSchema(
        data=PageResult(
            items=[RoleRead.model_validate(role) for role in roles],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post("", response_model=ResponseSchema[RoleRead], summary="创建角色")
async def create_role(
    data: RoleCreate,
    svc: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_user_with_permission("role:create")),
) -> ResponseSchema[RoleRead]:
    role = await svc.create(current_user, data)
    return ResponseSchema(data=RoleRead.model_validate(role))


@router.get("/{role_id}", response_model=ResponseSchema[RoleRead], summary="角色详情")
async def get_role(
    role_id: int,
    svc: RoleService = Depends(get_role_service),
    _: User = Depends(get_current_user_with_permission("role:read")),
) -> ResponseSchema[RoleRead]:
    role = await svc.get_role(role_id)
    return ResponseSchema(data=RoleRead.model_validate(role))


@router.put("/{role_id}", response_model=ResponseSchema[RoleRead], summary="更新角色")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    svc: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_user_with_permission("role:update")),
) -> ResponseSchema[RoleRead]:
    role = await svc.update(current_user, role_id, data)
    return ResponseSchema(data=RoleRead.model_validate(role))


@router.delete("/{role_id}", response_model=ResponseSchema[None], summary="删除角色")
async def delete_role(
    role_id: int,
    svc: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_user_with_permission("role:delete")),
) -> ResponseSchema[None]:
    await svc.delete(current_user, role_id)
    return ResponseSchema(data=None)


@router.put(
    "/{role_id}/permissions",
    response_model=ResponseSchema[RoleRead],
    summary="给角色分配权限",
)
async def assign_permissions(
    role_id: int,
    data: RoleAssignPermissions,
    svc: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_user_with_permission("role:assign_permissions")),
) -> ResponseSchema[RoleRead]:
    role = await svc.assign_permissions(current_user, role_id, data)
    return ResponseSchema(data=RoleRead.model_validate(role))
