from datetime import datetime

from pydantic import BaseModel, Field


class PromptRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str
    tags: list[str] | None = None
    content: str
    variables: list[str] | None = None
    version: str
    status: str
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    category: str = "general"
    tags: list[str] = []
    content: str = Field(min_length=1)
    variables: list[str] = []


class PromptUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    category: str | None = None
    tags: list[str] | None = None
    content: str | None = Field(None, min_length=1)
    variables: list[str] | None = None
    status: str | None = None


class PromptVersionRead(BaseModel):
    id: int
    prompt_id: int
    version: str
    content: str
    changelog: str | None = None
    is_current: bool
    published_by: str | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class PromptPublishRequest(BaseModel):
    changelog: str | None = Field(None, max_length=500)


class PromptTestRequest(BaseModel):
    variables: dict[str, str] = {}


class PromptTestResult(BaseModel):
    prompt_id: int
    rendered: str
    missing_variables: list[str] = []
