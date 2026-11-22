from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.model import User


class AuthUserRepository:
    """认证模块的数据访问：按用户名读取用户。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        return await self.db.scalar(select(User).where(User.username == username))

    async def save(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user
