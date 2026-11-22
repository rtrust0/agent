from datetime import datetime

from pydantic import BaseModel, Field


class PermissionRead(BaseModel):
    id: int
    code: str
    name: str
    module: str
    description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PermissionCreate(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=200)


class PermissionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=200)
