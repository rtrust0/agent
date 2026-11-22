from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiKeyRead(BaseModel):
    id: int
    name: str
    key: str
    permissions: str
    status: str
    rate_limit: int
    call_count: int
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    allowed_agent_ids: list[int] | None = None
    created_by: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permissions: str = Field("all", pattern="^(all|readonly|agent_only)$")
    rate_limit: int = Field(60, ge=1, le=100000)
    expires_at: datetime | None = None
    allowed_agent_ids: list[int] | None = None


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    permissions: str | None = Field(None, pattern="^(all|readonly|agent_only)$")
    status: str | None = Field(None, pattern="^(active|disabled|expired)$")
    rate_limit: int | None = Field(None, ge=1, le=100000)
    expires_at: datetime | None = None
    allowed_agent_ids: list[int] | None = None


class AlertRuleRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    condition: dict[str, Any] | None = None
    notification: dict[str, Any] | None = None
    status: str
    created_by: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=200)
    condition: dict[str, Any]
    notification: dict[str, Any] | None = None
    status: str = "enabled"


class AlertRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=200)
    condition: dict[str, Any] | None = None
    notification: dict[str, Any] | None = None
    status: str | None = Field(None, pattern="^(enabled|disabled)$")


class AlertRead(BaseModel):
    id: int
    type: str
    title: str
    message: str
    source: str
    severity: str
    status: str
    count: int
    first_occurred_at: datetime | None = None
    last_occurred_at: datetime | None = None
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class SettingsRead(BaseModel):
    id: int
    system_name: str
    system_description: str | None = None
    default_language: str
    default_model: str
    default_temperature: float
    default_max_tokens: int
    smtp_server: str | None = None
    smtp_port: int
    sender_email: str | None = None

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    system_name: str | None = Field(None, min_length=1, max_length=100)
    system_description: str | None = None
    default_language: str | None = None
    default_model: str | None = None
    default_temperature: float | None = Field(None, ge=0, le=2)
    default_max_tokens: int | None = Field(None, ge=1, le=200000)
    smtp_server: str | None = None
    smtp_port: int | None = Field(None, ge=1, le=65535)
    sender_email: str | None = None
