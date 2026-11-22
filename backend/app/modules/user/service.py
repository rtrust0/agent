from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PageParams, get_effective_permission_codes
from app.core.exceptions import BizException
from app.core.security import hash_password
from app.modules.audit.service import AuditService
from app.modules.role.model import Role
from app.modules.user.model import User
from app.modules.user.repository import UserRepository
from app.modules.user.schema import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)
        self.audit = AuditService(db)

    async def list_all(self, offset: int = 0, limit: int = 100) -> list[User]:
        return list(await self.repo.get_all(offset, limit))

    async def search_page(self, params: PageParams, current_user: User) -> tuple[list[User], int]:
        """用户目录属平台级数据：仅由 `user:list` 控制，不应用数据范围过滤。

        V3 §3.4.2 曾将用户模块列入数据范围，但与 `/users` 全量接口对登录用户开放、
        以及「只读角色有 user:list 却看不到任何用户」的体验冲突，故统一不做范围过滤。
        数据范围仍作用于业务数据（Agent / Prompt / 知识库 / 工具 / 对话 / 统计）。
        """
        return await self.repo.get_page(
            params.offset,
            params.page_size,
            params.keyword,
        )

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise BizException(code=404, message="用户不存在")
        return user

    async def create_user(self, actor: User, data: UserCreate) -> User:
        username = data.username.strip()
        email = data.email.strip()
        if not username:
            raise BizException(code=400, message="用户名不能为空")
        if not email:
            raise BizException(code=400, message="邮箱不能为空")
        if not data.password:
            raise BizException(code=400, message="密码不能为空")
        if await self.repo.get_by_username(username):
            raise BizException(code=400, message="用户名已存在")
        if await self.repo.get_by_email(email):
            raise BizException(code=400, message="邮箱已存在")

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(data.password),
            is_active=data.is_active,
            data_scope=data.data_scope,
            created_by=actor.id,
        )
        if data.role_ids:
            user.roles = await self._load_roles(data.role_ids)
        self.db.add(user)
        await self.db.flush()
        self.audit.record(
            actor,
            module="user",
            action="create",
            target_id=user.id,
            target_name=user.username,
            detail={"email": user.email, "data_scope": user.data_scope},
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, actor: User, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        before = {
            "email": user.email,
            "is_active": user.is_active,
            "data_scope": user.data_scope,
        }
        if data.email is not None:
            email = data.email.strip()
            existing = await self.repo.get_by_email(email)
            if existing and existing.id != user.id:
                raise BizException(code=400, message="邮箱已存在")
            user.email = email
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.data_scope is not None:
            user.data_scope = data.data_scope
        if data.password:
            user.hashed_password = hash_password(data.password)

        self.audit.record(
            actor,
            module="user",
            action="update",
            target_id=user.id,
            target_name=user.username,
            detail={
                "before": before,
                "after": {
                    "email": user.email,
                    "is_active": user.is_active,
                    "data_scope": user.data_scope,
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, actor: User, user_id: int) -> None:
        user = await self.get_user(user_id)
        self.audit.record(
            actor, module="user", action="delete", target_id=user.id, target_name=user.username
        )
        await self.repo.delete(user)
        await self.db.commit()

    async def assign_roles(self, actor: User, user_id: int, role_ids: list[int]) -> User:
        user = await self.get_user(user_id)
        user.roles = await self._load_roles(role_ids)
        self.audit.record(
            actor,
            module="user",
            action="assign",
            target_id=user.id,
            target_name=user.username,
            detail={"role_ids": sorted(role_ids)},
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_roles(self, user_id: int) -> list[Role]:
        user = await self.get_user(user_id)
        return list(user.roles)

    async def get_my_permissions(self, user: User) -> list[str]:
        return sorted(await get_effective_permission_codes(self.db, user))

    async def _load_roles(self, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        roles = (
            (await self.db.execute(select(Role).where(Role.id.in_(role_ids)))).scalars().all()
        )
        if len(roles) != len(set(role_ids)):
            raise BizException(code=400, message="角色不存在")
        return list(roles)
