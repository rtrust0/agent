from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_users: int = 0
    total_roles: int = 0
    total_permissions: int = 0
    total_agents: int = 0
    active_agents: int = 0
    total_models: int = 0
    total_knowledge_bases: int = 0
    total_tools: int = 0
    total_conversations: int = 0
    today_conversations: int = 0


class TrendPoint(BaseModel):
    date: str
    conversations: int = 0
    tokens: int = 0
    cost: float = 0


class TopAgent(BaseModel):
    agent_id: int
    name: str
    conversation_count: int = 0
    success_rate: float = 0


class AlertBrief(BaseModel):
    id: int
    title: str
    severity: str
    status: str
    source: str
    last_occurred_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResourceUsage(BaseModel):
    storage_mb: float = 0
    document_count: int = 0
    segment_count: int = 0
    token_usage_7d: int = 0
    api_calls_7d: int = 0
