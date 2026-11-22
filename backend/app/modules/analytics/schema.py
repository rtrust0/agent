from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_conversations: int = 0
    completed_conversations: int = 0
    error_conversations: int = 0
    total_tokens: int = 0
    total_cost: float = 0
    avg_latency_ms: int = 0
    success_rate: float = 0


class DailyMetric(BaseModel):
    date: str
    conversations: int = 0
    tokens: int = 0
    cost: float = 0


class AgentMetric(BaseModel):
    agent_id: int | None = None
    agent_name: str
    conversations: int = 0
    tokens: int = 0
    cost: float = 0
    avg_latency_ms: int = 0


class ModelMetric(BaseModel):
    model_id: int | None = None
    model_name: str
    conversations: int = 0
    tokens: int = 0
    cost: float = 0


class CostSummary(BaseModel):
    total_cost: float = 0
    avg_cost_per_conversation: float = 0
    daily: list[DailyMetric] = []


class EvaluationSummary(BaseModel):
    positive: int = 0
    negative: int = 0
    satisfaction_rate: float = 0
    avg_rating: float = 0
    needs_optimization: int = 0
