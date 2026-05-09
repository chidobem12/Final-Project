from __future__ import annotations

from typing import Iterable

from .models import CreateIncidentRequest, Incident, UpdateIncidentRequest, utc_now_iso


class IncidentStore:
    def __init__(self) -> None:
        self._incidents: list[Incident] = []
        self._counter = 1

    def _next_id(self) -> str:
        incident_id = f"INC-{self._counter:04d}"
        self._counter += 1
        return incident_id

    def list(self, status: str | None = None, severity: str | None = None) -> list[Incident]:
        data: Iterable[Incident] = self._incidents
        if status:
            data = [incident for incident in data if incident.status == status]
        if severity:
            data = [incident for incident in data if incident.severity == severity]
        return sorted(data, key=lambda incident: incident.created_at, reverse=True)

    def get(self, incident_id: str) -> Incident | None:
        return next((incident for incident in self._incidents if incident.id == incident_id), None)

    def create(self, req: CreateIncidentRequest) -> Incident:
        now = utc_now_iso()
        title = req.title or f"{req.attack_type} Attack from {req.source_ip}"
        incident = Incident(
            id=self._next_id(),
            title=title,
            severity=req.severity,
            status="OPEN",
            attack_type=req.attack_type,
            source_ip=req.source_ip,
            created_at=now,
            updated_at=now,
            event_ids=[req.event_id] if req.event_id else [],
            notes=req.notes,
        )
        self._incidents.append(incident)
        return incident

    def update(self, incident_id: str, req: UpdateIncidentRequest) -> Incident | None:
        incident = self.get(incident_id)
        if incident is None:
            return None

        updates = req.model_dump(exclude_unset=True)
        for key, value in updates.items():
            if key == "event_ids" and value:
                deduped = set(incident.event_ids)
                deduped.update(value)
                incident.event_ids = list(deduped)
            elif key == "status" and value:
                incident.status = value
                if value in {"RESOLVED", "FALSE_POSITIVE"}:
                    incident.resolved_at = utc_now_iso()
            else:
                setattr(incident, key, value)

        incident.updated_at = utc_now_iso()
        return incident

    def delete(self, incident_id: str) -> bool:
        incident = self.get(incident_id)
        if incident is None:
            return False
        self._incidents = [entry for entry in self._incidents if entry.id != incident_id]
        return True

    def unresolved_count(self) -> int:
        return sum(1 for incident in self._incidents if incident.status in {"OPEN", "INVESTIGATING"})

    def find_open_by_source(self, source_ip: str) -> Incident | None:
        return next(
            (
                incident
                for incident in self._incidents
                if incident.source_ip == source_ip and incident.status in {"OPEN", "INVESTIGATING"}
            ),
            None,
        )


incident_store = IncidentStore()
