from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Conversation(BaseModel):
    __tablename__ = "conversations"

    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_id: Mapped[int | None] = mapped_column(
        ForeignKey("models.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="completed")
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    needs_optimization: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    annotation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ConversationTurn(BaseModel):
    __tablename__ = "conversation_turns"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    trace: Mapped[dict | None] = mapped_column(JSON, nullable=True)
