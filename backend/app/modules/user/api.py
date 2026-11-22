from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import PageResult, ResponseSchema
from app.core.database import get_db
from app.core.deps import PageParams, get_current_user, get_current_user_with_permission
from app.modules.user.model import User
from app.modules.user.schema import (
    RoleBrief,
    UserAssignRoles,
    UserCreate,
    UserRead,
    UserUpdate,
    UserWithRolesRead,
)
from app.modules.user.service import UserService

router = APIRouter(prefix="/users", tags=["用户"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/me", response_model=ResponseSchema[UserWithRolesRead], summary="当前用户信息")
async def read_me(
    current_user: User = Depends(get_current_user),
) -> ResponseSchema[UserWithRolesRead]:
    return ResponseSchema(data=UserWithRolesRead.model_validate(current_user))


@router.get("/me/permissions", response_model=ResponseSchema[list[str]], summary="当前用户权限码")
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
) -> ResponseSchema[list[str]]:
    return ResponseSchema(data=await svc.get_my_permissions(current_user))


@router.get("/search", response_model=ResponseSchema[PageResult[UserRead]], summary="分页搜索用户")
async def search_users(
    params: PageParams = Depends(),
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user_with_permission("user:list")),
) -> ResponseSchema[PageResult[UserRead]]:
    users, total = await svc.search_page(params, current_user)
    return ResponseSchema(
        data=PageResult(
            items=[UserRead.model_validate(u) for u in users],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.get("", response_model=ResponseSchema[list[UserRead]], summary="用户全量列表")
async def list_users(
    offset: int = 0,
    limit: int = 100,
    svc: UserService = Depends(get_user_service),
    _: User = Depends(get_current_user),
) -> ResponseSchema[list[UserRead]]:
    users = await svc.list_all(offset, limit)
    return ResponseSchema(data=[UserRead.model_validate(u) for u in users])


@router.post("", response_model=ResponseSchema[UserWithRolesRead], summary="创建用户")
async def create_user(
    data: UserCreate,
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user_with_permission("user:create")),
) -> ResponseSchema[UserWithRolesRead]:
    user = await svc.create_user(current_user, data)
    return ResponseSchema(data=UserWithRolesRead.model_validate(user))


@router.get("/{user_id}", response_model=ResponseSchema[UserWithRolesRead], summary="用户详情")
async def get_user(
    user_id: int,
    svc: UserService = Depends(get_user_service),
    _: User = Depends(get_current_user_with_permission("user:read")),
) -> ResponseSchema[UserWithRolesRead]:
    user = await svc.get_user(user_id)
    return ResponseSchema(data=UserWithRolesRead.model_validate(user))


@router.put("/{user_id}", response_model=ResponseSchema[UserWithRolesRead], summary="更新用户")
async def update_user(
    user_id: int,
    data: UserUpdate,
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user_with_permission("user:update")),
) -> ResponseSchema[UserWithRolesRead]:
    user = await svc.update_user(current_user, user_id, data)
    return ResponseSchema(data=UserWithRolesRead.model_validate(user))


@router.delete("/{user_id}", response_model=ResponseSchema[None], summary="删除用户")
async def delete_user(
    user_id: int,
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user_with_permission("user:delete")),
) -> ResponseSchema[None]:
    await svc.delete_user(current_user, user_id)
    return ResponseSchema(data=None)


@router.put("/{user_id}/roles", response_model=ResponseSchema[UserWithRolesRead], summary="分配角色")
async def assign_roles(
    user_id: int,
    data: UserAssignRoles,
    svc: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user_with_permission("user:assign_roles")),
) -> ResponseSchema[UserWithRolesRead]:
    user = await svc.assign_roles(current_user, user_id, data.role_ids)
    return ResponseSchema(data=UserWithRolesRead.model_validate(user))


@router.get("/{user_id}/roles", response_model=ResponseSchema[list[RoleBrief]], summary="用户角色列表")
async def get_user_roles(
    user_id: int,
    svc: UserService = Depends(get_user_service),
    _: User = Depends(get_current_user_with_permission("user:read_roles")),
) -> ResponseSchema[list[RoleBrief]]:
    roles = await svc.get_user_roles(user_id)
    return ResponseSchema(data=[RoleBrief.model_validate(r) for r in roles])
