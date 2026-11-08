from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Permission(BaseModel):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
