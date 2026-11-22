from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.permission.model import Permission
from app.modules.role.model import Role
from app.modules.role.repository import RoleRepository
from app.modules.role.schema import RoleAssignPermissions, RoleCreate, RoleUpdate
from app.modules.user.model import User

BUILTIN_ROLES = {"super_admin"}


class RoleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RoleRepository(db)
        self.audit = AuditService(db)

    async def list_all(self) -> list[Role]:
        return list(await self.repo.get_all())

    async def search(self, params: PageParams) -> tuple[list[Role], int]:
        return await self.repo.get_page(params.offset, params.page_size, params.keyword)

    async def get_role(self, role_id: int) -> Role:
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise BizException(code=404, message="角色不存在")
        return role

    async def create(self, actor: User, data: RoleCreate) -> Role:
        code = data.code.strip()
        if await self.repo.get_by_code(code):
            raise BizException(code=400, message="角色编码已存在")
        role = Role(code=code, name=data.name.strip(), description=data.description)
        self.db.add(role)
        await self.db.flush()
        self.audit.record(
            actor,
            module="role",
            action="create",
            target_id=role.id,
            target_name=role.name,
            detail={"code": role.code},
        )
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update(self, actor: User, role_id: int, data: RoleUpdate) -> Role:
        role = await self.get_role(role_id)
        before = {"name": role.name, "description": role.description}
        if data.name is not None:
            role.name = data.name.strip()
        if data.description is not None:
            role.description = data.description
        self.audit.record(
            actor,
            module="role",
            action="update",
            target_id=role.id,
            target_name=role.name,
            detail={"before": before, "after": {"name": role.name, "description": role.description}},
        )
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, actor: User, role_id: int) -> None:
        role = await self.get_role(role_id)
        if role.code in BUILTIN_ROLES:
            raise BizException(code=400, message="内置角色不可删除")
        self.audit.record(
            actor, module="role", action="delete", target_id=role.id, target_name=role.name
        )
        await self.repo.delete(role)
        await self.db.commit()

    async def assign_permissions(
        self, actor: User, role_id: int, data: RoleAssignPermissions
    ) -> Role:
        role = await self.get_role(role_id)
        permissions = await self._load_permissions(data.permission_ids)
        role.permissions = permissions
        self.audit.record(
            actor,
            module="role",
            action="assign",
            target_id=role.id,
            target_name=role.name,
            detail={"permission_codes": sorted(p.code for p in permissions)},
        )
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def _load_permissions(self, permission_ids: list[int]) -> list[Permission]:
        if not permission_ids:
            return []
        rows = await self.db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        permissions = list(rows.scalars().all())
        if len(permissions) != len(set(permission_ids)):
            raise BizException(code=400, message="权限不存在")
        return permissions
