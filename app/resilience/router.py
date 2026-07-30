from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection
from app.resilience.service import create_shock, replay_shock


router = APIRouter(prefix="/api/resilience", tags=["resilience"])


class ShockRequest(BaseModel):
    instance_key: str
    shock_key: str
    scheduled_at: str
    severity: float = Field(ge=0, le=1)
    scope: dict = Field(default_factory=dict)
    parameters: dict = Field(default_factory=dict)
    source_type: str = "internal"
    source_id: str = ""
    branch_key: str = "main"
    random_seed: int = 0
    duration_minutes: Optional[int] = Field(default=None, ge=1)


class ShockReplayRequest(BaseModel):
    instance_key: str
    scheduled_at: str


@router.get("/definitions")
def list_shock_definitions():
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM shock_definitions ORDER BY shock_type, id"
            ).fetchall()
        ]


@router.get("/shocks")
def list_shocks(status: Optional[str] = None, limit: int = 100):
    with get_connection() as conn:
        if status is None:
            rows = conn.execute(
                "SELECT * FROM shock_instances ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM shock_instances WHERE status = ?
                ORDER BY id DESC LIMIT ?
                """,
                (status, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/shocks/{shock_id}")
def get_shock(shock_id: int):
    with get_connection() as conn:
        shock = conn.execute(
            "SELECT * FROM shock_instances WHERE id = ?", (shock_id,)
        ).fetchone()
        if not shock:
            raise HTTPException(status_code=404, detail="冲击不存在")
        impacts = conn.execute(
            "SELECT * FROM shock_impacts WHERE shock_instance_id = ? ORDER BY id",
            (shock_id,),
        ).fetchall()
        exposures = conn.execute(
            """
            SELECT * FROM resident_shock_exposures
            WHERE shock_instance_id = ? ORDER BY id
            """,
            (shock_id,),
        ).fetchall()
        recovery = conn.execute(
            "SELECT * FROM recovery_actions WHERE shock_instance_id = ? ORDER BY id",
            (shock_id,),
        ).fetchall()
        return {
            **dict(shock),
            "impacts": [dict(row) for row in impacts],
            "exposures": [dict(row) for row in exposures],
            "recovery_actions": [dict(row) for row in recovery],
        }


@router.post("/shocks")
def schedule_shock(payload: ShockRequest):
    try:
        with get_connection() as conn:
            result = create_shock(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/shocks/{shock_id}/replay")
def create_shock_replay(shock_id: int, payload: ShockReplayRequest):
    try:
        with get_connection() as conn:
            result = replay_shock(
                conn, shock_id, payload.instance_key, payload.scheduled_at
            )
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
