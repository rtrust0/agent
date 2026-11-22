import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.permission.model import Permission
from app.modules.permission.repository import PermissionRepository
from app.modules.permission.schema import PermissionCreate, PermissionUpdate
from app.modules.user.model import User

CODE_PATTERN = re.compile(r"^[a-z][a-z_]*:[a-z][a-z_]*$")


class PermissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PermissionRepository(db)
        self.audit = AuditService(db)

    async def list_all(self) -> list[Permission]:
        return list(await self.repo.get_all())

    async def search(self, params: PageParams) -> tuple[list[Permission], int]:
        return await self.repo.get_page(params.offset, params.page_size, params.keyword)

    async def get_permission(self, permission_id: int) -> Permission:
        permission = await self.repo.get_by_id(permission_id)
        if not permission:
            raise BizException(code=404, message="权限不存在")
        return permission

    async def create(self, actor: User, data: PermissionCreate) -> Permission:
        code = data.code.strip()
        if not CODE_PATTERN.match(code):
            raise BizException(code=400, message="权限码格式应为 模块:操作（全小写，下划线分隔）")
        if await self.repo.get_by_code(code):
            raise BizException(code=400, message="权限码已存在")
        permission = Permission(
            code=code, name=data.name.strip(), description=data.description
        )
        self.db.add(permission)
        await self.db.flush()
        self.audit.record(
            actor,
            module="permission",
            action="create",
            target_id=permission.id,
            target_name=permission.name,
            detail={"code": permission.code},
        )
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def update(
        self, actor: User, permission_id: int, data: PermissionUpdate
    ) -> Permission:
        permission = await self.get_permission(permission_id)
        before = {"name": permission.name, "description": permission.description}
        if data.name is not None:
            permission.name = data.name.strip()
        if data.description is not None:
            permission.description = data.description
        self.audit.record(
            actor,
            module="permission",
            action="update",
            target_id=permission.id,
            target_name=permission.name,
            detail={
                "before": before,
                "after": {"name": permission.name, "description": permission.description},
            },
        )
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def delete(self, actor: User, permission_id: int) -> None:
        permission = await self.get_permission(permission_id)
        self.audit.record(
            actor,
            module="permission",
            action="delete",
            target_id=permission.id,
            target_name=permission.code,
        )
        await self.repo.delete(permission)
        await self.db.commit()
