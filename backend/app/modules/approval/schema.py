from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalApply(BaseModel):
    permission_code: str
    reason: str
    expired_at: datetime | None = None


class ApprovalAuditRequest(BaseModel):
    approved: bool
    comment: str | None = Field(None, max_length=500)
    expired_at: datetime | None = None


class ApplicationRead(BaseModel):
    id: int
    applicant_id: int
    applicant_name: str
    permission_code: str
    reason: str
    status: str
    approver_id: int | None = None
    approver_name: str | None = None
    approved_at: datetime | None = None
    expired_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
