from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.db import get_connection
from app.social_institutions.service import submit_appeal, submit_institutional_case


router = APIRouter(prefix="/api/social-institutions", tags=["social-institutions"])


def _rows(query, params=()):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


@router.get("/claims")
def list_claims(limit: int = Query(100, ge=1, le=500)):
    return _rows("SELECT * FROM information_claims ORDER BY id DESC LIMIT ?", (limit,))


@router.get("/transmissions")
def list_transmissions(
    resident_id: Optional[int] = None,
    limit: int = Query(200, ge=1, le=1000),
):
    if resident_id is None:
        return _rows("SELECT * FROM information_transmissions ORDER BY id DESC LIMIT ?", (limit,))
    return _rows(
        """
        SELECT * FROM information_transmissions
        WHERE sender_resident_id = ? OR recipient_resident_id = ?
        ORDER BY id DESC LIMIT ?
        """,
        (resident_id, resident_id, limit),
    )


@router.get("/exposures")
def list_exposures(resident_id: Optional[int] = None, limit: int = Query(200, ge=1, le=1000)):
    if resident_id is None:
        return _rows("SELECT * FROM information_exposures ORDER BY id DESC LIMIT ?", (limit,))
    return _rows(
        "SELECT * FROM information_exposures WHERE resident_id = ? ORDER BY id DESC LIMIT ?",
        (resident_id, limit),
    )


@router.get("/beliefs")
def list_beliefs(resident_id: Optional[int] = None, limit: int = Query(200, ge=1, le=1000)):
    if resident_id is None:
        return _rows("SELECT * FROM information_beliefs ORDER BY last_updated_at DESC LIMIT ?", (limit,))
    return _rows(
        "SELECT * FROM information_beliefs WHERE resident_id = ? ORDER BY last_updated_at DESC LIMIT ?",
        (resident_id, limit),
    )


@router.get("/rules")
def list_rules():
    return _rows("SELECT * FROM institutional_rules ORDER BY id")


@router.get("/cases")
def list_cases(resident_id: Optional[int] = None, limit: int = Query(200, ge=1, le=1000)):
    if resident_id is None:
        return _rows("SELECT * FROM institutional_cases ORDER BY id DESC LIMIT ?", (limit,))
    return _rows(
        "SELECT * FROM institutional_cases WHERE subject_resident_id = ? ORDER BY id DESC LIMIT ?",
        (resident_id, limit),
    )


@router.get("/decisions")
def list_decisions(limit: int = Query(200, ge=1, le=1000)):
    return _rows("SELECT * FROM institutional_decisions ORDER BY id DESC LIMIT ?", (limit,))


@router.get("/power")
def list_power_profiles():
    return _rows("SELECT * FROM resident_power_profiles ORDER BY resident_id")


@router.get("/trust-events")
def list_trust_events(resident_id: Optional[int] = None, limit: int = Query(200, ge=1, le=1000)):
    if resident_id is None:
        return _rows("SELECT * FROM institutional_trust_events ORDER BY id DESC LIMIT ?", (limit,))
    return _rows(
        "SELECT * FROM institutional_trust_events WHERE resident_id = ? ORDER BY id DESC LIMIT ?",
        (resident_id, limit),
    )


class CaseRequest(BaseModel):
    case_key: str = Field(min_length=1, max_length=240)
    rule_key: str = Field(min_length=1, max_length=120)
    subject_resident_id: int
    organization_id: Optional[int] = None
    evidence: dict = Field(default_factory=dict)
    requested_outcome: str = ""
    bypass_attempted: bool = False


@router.post("/cases")
def create_case(payload: CaseRequest):
    with get_connection() as conn:
        result = submit_institutional_case(conn, **payload.model_dump())
        conn.commit()
        return result


class AppealRequest(BaseModel):
    resident_id: int
    reason: str = Field(min_length=1, max_length=1000)


@router.post("/cases/{case_id}/appeal")
def create_appeal(case_id: int, payload: AppealRequest):
    with get_connection() as conn:
        result = submit_appeal(
            conn,
            parent_case_id=case_id,
            resident_id=payload.resident_id,
            reason=payload.reason,
        )
        conn.commit()
        return result
