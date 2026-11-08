from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.core.security import create_token, verify_password
from app.modules.user.model import User


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def login(self, username: str, password: str) -> tuple[str, User]:
        user = await self.db.scalar(select(User).where(User.username == username))
        if not user or not verify_password(password, user.hashed_password):
            raise BizException(code=401, message="用户名或密码错误")
        if not user.is_active:
            raise BizException(code=401, message="账号已被禁用")

        user.last_login = datetime.now()
        await self.db.commit()
        return create_token(user.id), user
