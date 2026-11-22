from datetime import datetime

from pydantic import BaseModel


class RoleBrief(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    data_scope: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserWithRolesRead(UserRead):
    roles: list[RoleBrief] = []


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role_ids: list[int] = []
    is_active: bool = True
    data_scope: str = "own"


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None
    data_scope: str | None = None


class UserAssignRoles(BaseModel):
    role_ids: list[int] = []
