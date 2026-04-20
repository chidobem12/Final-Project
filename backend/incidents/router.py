from fastapi import APIRouter, Depends, HTTPException

from ..auth.router import get_current_user

from .models import CreateIncidentRequest, Incident, UpdateIncidentRequest
from .store import incident_store


router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("", response_model=Incident)
async def create_incident(req: CreateIncidentRequest, current_user: dict = Depends(get_current_user)):
    _ = current_user
    return incident_store.create(req)


@router.get("", response_model=list[Incident])
async def list_incidents(
    status: str | None = None,
    severity: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    _ = current_user
    return incident_store.list(status=status, severity=severity)


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str, current_user: dict = Depends(get_current_user)):
    _ = current_user
    incident = incident_store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: str,
    req: UpdateIncidentRequest,
    current_user: dict = Depends(get_current_user),
):
    _ = current_user
    incident = incident_store.update(incident_id, req)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.delete("/{incident_id}")
async def delete_incident(incident_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    ok = incident_store.delete(incident_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "deleted", "incident_id": incident_id}
