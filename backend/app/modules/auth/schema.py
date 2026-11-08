from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBrief(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    data_scope: str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    user: UserBrief
