from decimal import Decimal

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class ModelProvider(BaseModel):
    __tablename__ = "model_providers"

    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="disconnected")
    endpoint: Mapped[str] = mapped_column(String(500))
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    models: Mapped[list["LLMModel"]] = relationship(
        "LLMModel", back_populates="provider", cascade="all, delete-orphan"
    )

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)


class LLMModel(BaseModel):
    __tablename__ = "models"

    name: Mapped[str] = mapped_column(String(100))
    model_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("model_providers.id", ondelete="CASCADE"), index=True
    )
    capabilities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    context_length: Mapped[int] = mapped_column(Integer, default=4096)
    status: Mapped[str] = mapped_column(String(50), default="available")
    input_price: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    output_price: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    provider: Mapped[ModelProvider] = relationship("ModelProvider", back_populates="models", lazy="selectin")

    @property
    def provider_name(self) -> str | None:
        return self.provider.name if self.provider else None
