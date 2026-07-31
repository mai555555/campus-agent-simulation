from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection
from app.population.service import (
    get_resident_population_history,
    schedule_population_event,
)


router = APIRouter(prefix="/api/population", tags=["population"])


class PopulationEventRequest(BaseModel):
    event_key: str
    event_type: str
    effective_at: str
    resident_id: Optional[int] = None
    payload: dict = Field(default_factory=dict)
    source_type: str = "internal"
    source_id: str = ""
    branch_key: str = "main"


@router.get("/profiles")
def list_population_profiles(status: Optional[str] = None):
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                """
                SELECT profile.*, resident.name, resident.role, resident.location
                FROM population_profiles profile
                JOIN residents resident ON resident.id = profile.resident_id
                WHERE profile.lifecycle_status = ?
                ORDER BY profile.resident_id
                """,
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT profile.*, resident.name, resident.role, resident.location
                FROM population_profiles profile
                JOIN residents resident ON resident.id = profile.resident_id
                ORDER BY profile.resident_id
                """
            ).fetchall()
        return [dict(row) for row in rows]


@router.post("/events")
def create_population_event(payload: PopulationEventRequest):
    try:
        with get_connection() as conn:
            result = schedule_population_event(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/events")
def list_population_events(limit: int = 100):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM population_events ORDER BY id DESC LIMIT ?",
            (min(max(limit, 1), 500),),
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/residents/{resident_id}/history")
def resident_population_history(resident_id: int):
    with get_connection() as conn:
        result = get_resident_population_history(conn, resident_id)
        if result is None:
            raise HTTPException(status_code=404, detail="居民生命周期档案不存在")
        return result
