from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.core.security import create_token, verify_password
from app.modules.audit.service import AuditService
from app.modules.auth.repository import AuthUserRepository
from app.modules.user.model import User


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuthUserRepository(db)
        self.audit = AuditService(db)

    async def login(self, username: str, password: str) -> tuple[str, User]:
        user = await self.repo.get_by_username(username.strip())
        if not user or not verify_password(password, user.hashed_password):
            raise BizException(code=401, message="用户名或密码错误")
        if not user.is_active:
            raise BizException(code=401, message="账号已被禁用")

        user.last_login = datetime.now()
        self.audit.record(user, module="auth", action="login", target_id=user.id, target_name=user.username)
        await self.repo.save(user)
        return create_token(user.id), user
