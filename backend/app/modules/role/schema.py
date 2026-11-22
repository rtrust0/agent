from datetime import datetime

from pydantic import BaseModel, Field


class PermissionBrief(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class RoleRead(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    created_at: datetime | None = None
    permissions: list[PermissionBrief] = []

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=200)


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=200)


class RoleAssignPermissions(BaseModel):
    permission_ids: list[int] = []
