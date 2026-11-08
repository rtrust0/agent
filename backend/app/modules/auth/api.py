from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import ResponseSchema
from app.core.database import get_db
from app.modules.auth.schema import LoginRequest, LoginResponse, UserBrief
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ResponseSchema[LoginResponse], summary="用户登录")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> ResponseSchema[LoginResponse]:
    token, user = await AuthService(db).login(data.username, data.password)
    return ResponseSchema(
        data=LoginResponse(token=token, user=UserBrief.model_validate(user))
    )
