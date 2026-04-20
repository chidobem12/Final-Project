from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["CRITICAL", "HIGH", "MEDIUM"]
Status = Literal["OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"]


class Incident(BaseModel):
    id: str
    title: str
    severity: Severity
    status: Status = "OPEN"
    attack_type: str
    source_ip: str
    created_at: str
    updated_at: str
    event_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    assigned_to: str | None = None
    resolved_at: str | None = None
    resolution_note: str | None = None


class CreateIncidentRequest(BaseModel):
    title: str | None = None
    severity: Severity
    attack_type: str
    source_ip: str
    event_id: str | None = None
    notes: str = ""


class UpdateIncidentRequest(BaseModel):
    status: Status | None = None
    notes: str | None = None
    assigned_to: str | None = None
    resolution_note: str | None = None
    event_ids: list[str] | None = None


class IncidentAutoCreateRequest(BaseModel):
    severity: Severity
    attack_type: str
    source_ip: str
    event_id: str


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
