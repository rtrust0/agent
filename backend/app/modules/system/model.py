from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class ApiKey(BaseModel):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100))
    key: Mapped[str] = mapped_column(String(100), unique=True)
    permissions: Mapped[str] = mapped_column(String(20), default="all")
    status: Mapped[str] = mapped_column(String(20), default="active")
    rate_limit: Mapped[int] = mapped_column(Integer, default=60)
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    allowed_agent_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class AlertRule(BaseModel):
    __tablename__ = "alert_rules"

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    condition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notification: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="enabled")
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Alert(BaseModel):
    __tablename__ = "alerts"

    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    first_occurred_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_occurred_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    system_name: Mapped[str] = mapped_column(String(100), default="辰光Agent平台")
    system_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_language: Mapped[str] = mapped_column(String(20), default="zh-CN")
    default_model: Mapped[str] = mapped_column(String(100), default="GPT-4")
    default_temperature: Mapped[float] = mapped_column(Float, default=0.7)
    default_max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    smtp_server: Mapped[str | None] = mapped_column(String(200), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    sender_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
