from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConversationRead(BaseModel):
    id: int
    agent_id: int | None = None
    agent_name: str | None = None
    model_id: int | None = None
    user_id: int | None = None
    status: str
    turn_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: float
    latency_ms: int
    satisfaction: str | None = None
    rating: int | None = None
    tags: list[str] | None = None
    needs_optimization: bool | None = None
    annotation: dict[str, Any] | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationTurnRead(BaseModel):
    id: int
    conversation_id: int
    position: int
    role: str
    content: str
    timestamp: datetime | None = None
    trace: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class ConversationAnnotate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    tags: list[str] | None = None
    needs_optimization: bool | None = None
    annotation: dict[str, Any] | None = None
    satisfaction: str | None = Field(None, pattern="^(positive|negative)$")


class ExportResult(BaseModel):
    content: str
    filename: str
