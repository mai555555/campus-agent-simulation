from __future__ import annotations

from typing import Optional

import json

from fastapi import APIRouter, Query

from app.budget.service import calculate_budget_state
from app.db import get_connection


router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("/residents/{resident_id}")
def get_resident_budget(resident_id: int):
    with get_connection() as conn:
        return calculate_budget_state(conn, resident_id)


@router.get("/snapshots")
def list_budget_snapshots(
    resident_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE snapshot.resident_id = ?", (resident_id,))
        rows = conn.execute(
            f"""
            SELECT snapshot.*, resident.name AS resident_name
            FROM household_budget_snapshots snapshot
            JOIN residents resident ON resident.id = snapshot.resident_id
            {where}
            ORDER BY snapshot.budget_date DESC, snapshot.id DESC
            LIMIT {int(limit)}
            """,
            params,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            result.append(item)
        return result


@router.get("/savings-transfers")
def list_savings_transfers(
    resident_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE transfer.resident_id = ?", (resident_id,))
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT transfer.*, resident.name AS resident_name
                FROM savings_transfers transfer
                JOIN residents resident ON resident.id = transfer.resident_id
                {where}
                ORDER BY transfer.id DESC LIMIT {int(limit)}
                """,
                params,
            ).fetchall()
        ]


@router.get("/choices")
def list_choice_evaluations(
    resident_id: Optional[int] = None,
    decision: Optional[str] = Query(
        default=None, pattern="^(allowed|rejected|deferred)$"
    ),
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        clauses, params = [], []
        if resident_id is not None:
            clauses.append("choice.resident_id = ?")
            params.append(resident_id)
        if decision:
            clauses.append("choice.decision = ?")
            params.append(decision)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT choice.*, resident.name AS resident_name
                FROM choice_evaluations choice
                JOIN residents resident ON resident.id = choice.resident_id
                {where}
                ORDER BY choice.id DESC LIMIT {int(limit)}
                """,
                tuple(params),
            ).fetchall()
        ]
