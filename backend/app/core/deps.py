from datetime import datetime
from typing import TYPE_CHECKING, AsyncGenerator

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.security import decode_token

if TYPE_CHECKING:
    from app.modules.user.model import User

security = HTTPBearer(auto_error=False)


class PageParams:
    """通用分页参数，通过 Depends() 注入。"""

    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        keyword: str | None = Query(None),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.keyword = keyword

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> "User":
    """从 JWT 解析当前登录用户；缺失/无效 token 抛 401。"""
    from app.modules.user.model import User

    if credentials is None:
        raise BizException(code=401, message="未登录或 token 已过期")
    payload = decode_token(credentials.credentials)
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise BizException(code=401, message="未登录或 token 已过期") from exc

    user = await db.get(User, user_id)
    if not user:
        raise BizException(code=401, message="用户不存在")
    if not user.is_active:
        raise BizException(code=401, message="账号已被禁用")
    return user


def get_user_permission_codes(user: "User") -> set[str]:
    """遍历 user.roles → role.permissions，返回去重权限码集合（不含审批直接授权）。"""
    codes: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            codes.add(permission.code)
    return codes


async def get_effective_permission_codes(db: AsyncSession, user: "User") -> set[str]:
    """有效权限 = 角色权限 ∪ 已通过且未过期的权限申请；超管返回库中全部权限码。

    V3 §3.6.3 的「到期自动回收」由这里的过期判断实现：过期申请不再计入有效权限。
    """
    from app.modules.approval.model import PermissionApplication
    from app.modules.permission.model import Permission

    if user.is_superuser:
        rows = await db.execute(select(Permission.code))
        return set(rows.scalars().all())

    codes = get_user_permission_codes(user)
    granted = await db.execute(
        select(PermissionApplication.permission_code).where(
            PermissionApplication.applicant_id == user.id,
            PermissionApplication.status == "approved",
            or_(
                PermissionApplication.expired_at.is_(None),
                PermissionApplication.expired_at > datetime.now(),
            ),
        )
    )
    codes |= set(granted.scalars().all())
    return codes


def get_current_user_with_permission(permission_code: str):
    """返回携带权限码的依赖：超管放行，否则校验有效权限码。"""

    async def _check(
        current_user: "User" = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> "User":
        if current_user.is_superuser:
            return current_user
        codes = await get_effective_permission_codes(db, current_user)
        if permission_code not in codes:
            raise BizException(code=403, message="没有权限执行该操作")
        return current_user

    return _check


__all__ = [
    "PageParams",
    "get_db",
    "get_current_user",
    "get_user_permission_codes",
    "get_effective_permission_codes",
    "get_current_user_with_permission",
]
