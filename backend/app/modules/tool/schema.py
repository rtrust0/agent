from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

TOOL_TYPES = {"builtin", "http_api", "custom_function"}


class ToolRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    type: str
    status: str
    config: dict[str, Any] | None = None
    function_definition: dict[str, Any] | None = None
    call_count_7d: int
    success_rate: float
    avg_latency: int
    created_by: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    type: str = "http_api"
    config: dict[str, Any] | None = None
    function_definition: dict[str, Any] | None = None
    status: str = "disabled"


class ToolUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    type: str | None = None
    config: dict[str, Any] | None = None
    function_definition: dict[str, Any] | None = None


class ToolTestRequest(BaseModel):
    arguments: dict[str, Any] = {}


class ToolTestResult(BaseModel):
    tool_id: int
    success: bool
    message: str
    latency_ms: int = 0


class ToolLogItem(BaseModel):
    id: int
    success: bool
    latency_ms: int
    created_at: datetime | None = None


class ToolLogSummary(BaseModel):
    call_count_7d: int
    success_rate: float
    avg_latency: int


class ToolLogPage(BaseModel):
    items: list[ToolLogItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: ToolLogSummary | None = None
