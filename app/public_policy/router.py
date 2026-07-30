from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_connection


router = APIRouter(prefix="/api/public-policy", tags=["public-policy"])


def _rows(query: str, params=()):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


@router.get("/services")
def list_public_services():
    return _rows("SELECT * FROM public_services ORDER BY id")


@router.get("/operations")
def list_public_service_operations(limit: int = Query(100, ge=1, le=500)):
    return _rows(
        """
        SELECT operation.*, service.service_key, service.name
        FROM public_service_operations operation
        JOIN public_services service ON service.id = operation.service_id
        ORDER BY operation.operation_date DESC, operation.id DESC LIMIT ?
        """,
        (limit,),
    )


@router.get("/usages")
def list_public_service_usages(
    resident_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
):
    if resident_id is None:
        return _rows(
            "SELECT * FROM public_service_usages ORDER BY id DESC LIMIT ?", (limit,)
        )
    return _rows(
        """
        SELECT * FROM public_service_usages
        WHERE resident_id = ? ORDER BY id DESC LIMIT ?
        """,
        (resident_id, limit),
    )


@router.get("/externalities")
def list_externalities(limit: int = Query(100, ge=1, le=500)):
    return _rows("SELECT * FROM externality_events ORDER BY id DESC LIMIT ?", (limit,))


@router.get("/exposures")
def list_externality_exposures(
    resident_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
):
    if resident_id is None:
        return _rows(
            "SELECT * FROM externality_exposures ORDER BY id DESC LIMIT ?", (limit,)
        )
    return _rows(
        """
        SELECT * FROM externality_exposures
        WHERE resident_id = ? ORDER BY id DESC LIMIT ?
        """,
        (resident_id, limit),
    )


@router.get("/policies")
def list_policy_instruments():
    return _rows("SELECT * FROM policy_instruments ORDER BY id")


@router.get("/benefits")
def list_policy_benefits(
    resident_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
):
    if resident_id is None:
        return _rows("SELECT * FROM policy_benefits ORDER BY id DESC LIMIT ?", (limit,))
    return _rows(
        "SELECT * FROM policy_benefits WHERE resident_id = ? ORDER BY id DESC LIMIT ?",
        (resident_id, limit),
    )


@router.get("/outcomes")
def list_policy_outcomes(limit: int = Query(200, ge=1, le=1000)):
    return _rows(
        "SELECT * FROM policy_outcome_snapshots ORDER BY id DESC LIMIT ?", (limit,)
    )
