from datetime import datetime

from pydantic import BaseModel, Field


class ProviderRead(BaseModel):
    id: int
    name: str
    type: str
    status: str
    endpoint: str
    description: str | None = None
    has_api_key: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    endpoint: str = Field(min_length=1, max_length=500)
    api_key: str | None = None
    description: str | None = Field(None, max_length=500)


class ProviderUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    type: str | None = Field(None, min_length=1, max_length=50)
    endpoint: str | None = Field(None, min_length=1, max_length=500)
    api_key: str | None = None
    description: str | None = Field(None, max_length=500)


class ModelRead(BaseModel):
    id: int
    name: str
    model_id: str
    provider_id: int
    provider_name: str | None = None
    capabilities: list[str] | None = None
    context_length: int
    status: str
    input_price: float
    output_price: float
    currency: str
    is_default: bool
    description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    model_id: str = Field(min_length=1, max_length=100)
    provider_id: int
    capabilities: list[str] = []
    context_length: int = Field(4096, ge=1)
    status: str = "available"
    input_price: float = Field(0, ge=0)
    output_price: float = Field(0, ge=0)
    currency: str = "USD"
    is_default: bool = False
    description: str | None = None


class ModelUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    capabilities: list[str] | None = None
    context_length: int | None = Field(None, ge=1)
    status: str | None = None
    input_price: float | None = Field(None, ge=0)
    output_price: float | None = Field(None, ge=0)
    currency: str | None = None
    is_default: bool | None = None
    description: str | None = None


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int = 0
