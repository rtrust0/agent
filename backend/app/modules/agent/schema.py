from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

AGENT_TYPES = {"conversation", "tool", "analysis", "creative", "workflow"}


class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    type: str
    status: str
    model_id: int | None = None
    config: dict[str, Any] | None = None
    success_rate: float
    call_count_7d: int
    version: str
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    type: str = "conversation"
    model_id: int | None = None
    config: dict[str, Any] | None = None


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    type: str | None = None
    model_id: int | None = None
    config: dict[str, Any] | None = None
    status: str | None = None


class AgentVersionRead(BaseModel):
    id: int
    agent_id: int
    version: str
    config: dict[str, Any] | None = None
    changelog: str | None = None
    is_current: bool
    published_by: str | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class AgentPublishRequest(BaseModel):
    changelog: str | None = Field(None, max_length=500)


class AgentTestRequest(BaseModel):
    input: str = Field(min_length=1, max_length=2000)


class AgentTestResult(BaseModel):
    agent_id: int
    success: bool
    output: str
    latency_ms: int = 0


class AgentMonitorRead(BaseModel):
    agent_id: int
    name: str
    status: str
    call_count_7d: int
    success_rate: float
    avg_latency_ms: int
    version: str
    recent_errors: list[str] = []
