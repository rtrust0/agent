from typing import TYPE_CHECKING, AsyncGenerator

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
    """遍历 user.roles → role.permissions，返回去重权限码集合。"""
    codes: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            codes.add(permission.code)
    return codes


def get_current_user_with_permission(permission_code: str):
    """返回携带权限码的依赖：超管放行，否则校验权限码。"""
    from app.core.security import decode_token as _decode  # noqa: F401

    async def _check(current_user: "User" = Depends(get_current_user)) -> "User":
        if current_user.is_superuser:
            return current_user
        if permission_code not in get_user_permission_codes(current_user):
            raise BizException(code=403, message="没有权限执行该操作")
        return current_user

    return _check


__all__ = [
    "PageParams",
    "get_db",
    "get_current_user",
    "get_user_permission_codes",
    "get_current_user_with_permission",
]
