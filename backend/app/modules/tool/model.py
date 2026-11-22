from decimal import Decimal

from sqlalchemy import JSON, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Tool(BaseModel):
    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="disabled")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    function_definition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    call_count_7d: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    avg_latency: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
