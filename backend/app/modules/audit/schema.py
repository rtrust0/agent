import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None = None
    username: str
    action: str
    module: str
    target_id: str | None = None
    target_name: str | None = None
    detail: dict[str, Any] | list[Any] | None = None
    ip_address: str = ""
    user_agent: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("detail", mode="before")
    @classmethod
    def _parse_detail(cls, value: Any) -> Any:
        if isinstance(value, str) and value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {"raw": value}
        return value


class ExportResult(BaseModel):
    content: str
    filename: str
