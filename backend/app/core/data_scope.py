"""资源级数据权限（V3 §3.4）。

规则：
- `own`  ：仅本人创建的数据（业务表 created_by 存用户名，users.created_by 存用户 ID）
- `dept` ：本部门数据；业务表暂无 department_id，降级为本人数据（见台账 Ruling）
- `all`  ：不过滤；超管等价 all

过滤条件在 Service 层拼装（不在 Controller），越权访问详情/写操作抛 403。
"""

from typing import Any

from sqlalchemy.sql.elements import ColumnElement

from app.core.exceptions import BizException

SCOPE_OWN = "own"
SCOPE_DEPT = "dept"
SCOPE_ALL = "all"
VALID_SCOPES = {SCOPE_OWN, SCOPE_DEPT, SCOPE_ALL}


def scope_value(user: Any, owner_is_user_id: bool) -> Any:
    """当前用户在其数据归属字段上的取值。"""
    return user.id if owner_is_user_id else user.username


def scope_condition(
    model: Any,
    user: Any,
    owner_field: str = "created_by",
    *,
    owner_is_user_id: bool = False,
) -> ColumnElement[bool] | None:
    """返回列表查询需要追加的条件；None 表示不过滤。"""
    if user.is_superuser or getattr(user, "data_scope", SCOPE_OWN) == SCOPE_ALL:
        return None
    column = getattr(model, owner_field, None)
    if column is None:
        return None
    return column == scope_value(user, owner_is_user_id)


def in_scope(
    obj: Any,
    user: Any,
    owner_field: str = "created_by",
    *,
    owner_is_user_id: bool = False,
) -> bool:
    if user.is_superuser or getattr(user, "data_scope", SCOPE_OWN) == SCOPE_ALL:
        return True
    return getattr(obj, owner_field, None) == scope_value(user, owner_is_user_id)


def assert_in_scope(
    obj: Any,
    user: Any,
    owner_field: str = "created_by",
    *,
    owner_is_user_id: bool = False,
    message: str = "没有权限访问该数据",
) -> None:
    if not in_scope(obj, user, owner_field, owner_is_user_id=owner_is_user_id):
        raise BizException(code=403, message=message)
