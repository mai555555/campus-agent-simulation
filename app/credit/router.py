from __future__ import annotations

from typing import Optional

import json

from fastapi import APIRouter, Query

from app.credit.service import available_credit
from app.db import get_connection


router = APIRouter(prefix="/api/credit", tags=["credit"])


def _decode(rows, *json_fields):
    result = []
    for row in rows:
        item = dict(row)
        for field in json_fields:
            if field in item:
                item[field.removesuffix("_json")] = json.loads(
                    item.pop(field) or "{}"
                )
        result.append(item)
    return result


@router.get("/products")
def list_credit_products():
    with get_connection() as conn:
        return _decode(
            conn.execute(
                "SELECT * FROM credit_products ORDER BY product_type, id"
            ).fetchall(),
            "metadata_json",
        )


@router.get("/profiles")
def list_credit_profiles(resident_id: Optional[int] = None):
    with get_connection() as conn:
        if resident_id is not None:
            return available_credit(conn, resident_id)
        return _decode(
            conn.execute(
                """
                SELECT profile.*, resident.name AS resident_name
                FROM credit_profiles profile
                JOIN residents resident ON resident.id = profile.resident_id
                ORDER BY profile.credit_score DESC, profile.resident_id
                """
            ).fetchall(),
            "metadata_json",
        )


@router.get("/contracts")
def list_credit_contracts(
    resident_id: Optional[int] = None,
    status: Optional[str] = Query(
        default=None,
        pattern="^(active|late|defaulted|paid|restructured)$",
    ),
    limit: int = Query(default=100, ge=1, le=500),
):
    with get_connection() as conn:
        clauses, params = [], []
        if resident_id is not None:
            clauses.append("contract.borrower_resident_id = ?")
            params.append(resident_id)
        if status:
            clauses.append("contract.status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return _decode(
            conn.execute(
                f"""
                SELECT contract.*, product.name AS product_name,
                       resident.name AS borrower_name
                FROM credit_contracts contract
                JOIN credit_products product ON product.id = contract.product_id
                JOIN residents resident ON resident.id = contract.borrower_resident_id
                {where}
                ORDER BY contract.id DESC LIMIT {int(limit)}
                """,
                tuple(params),
            ).fetchall(),
            "collateral_json",
            "metadata_json",
        )


@router.get("/installments")
def list_credit_installments(
    contract_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    with get_connection() as conn:
        where, params = ("", ())
        if contract_id is not None:
            where, params = ("WHERE installment.contract_id = ?", (contract_id,))
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT installment.*, contract.contract_key
                FROM credit_installments installment
                JOIN credit_contracts contract ON contract.id = installment.contract_id
                {where}
                ORDER BY installment.due_date, installment.id
                LIMIT {int(limit)}
                """,
                params,
            ).fetchall()
        ]


@router.get("/payments")
def list_credit_payments(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT payment.*, contract.contract_key
                FROM credit_payments payment
                JOIN credit_contracts contract ON contract.id = payment.contract_id
                ORDER BY payment.id DESC LIMIT {int(limit)}
                """
            ).fetchall()
        ]


@router.get("/events")
def list_credit_events(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        return _decode(
            conn.execute(
                f"""
                SELECT event.*, resident.name AS resident_name
                FROM credit_events event
                JOIN residents resident ON resident.id = event.resident_id
                ORDER BY event.id DESC LIMIT {int(limit)}
                """
            ).fetchall(),
            "details_json",
        )


@router.get("/savings-goals")
def list_savings_goals(resident_id: Optional[int] = None):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE goal.resident_id = ?", (resident_id,))
        return _decode(
            conn.execute(
                f"""
                SELECT goal.*, resident.name AS resident_name
                FROM savings_goals goal
                JOIN residents resident ON resident.id = goal.resident_id
                {where}
                ORDER BY goal.priority DESC, goal.id
                """,
                params,
            ).fetchall(),
            "metadata_json",
        )


@router.get("/risk-profiles")
def list_risk_profiles():
    with get_connection() as conn:
        return _decode(
            conn.execute(
                """
                SELECT profile.*, resident.name AS resident_name
                FROM household_risk_profiles profile
                JOIN residents resident ON resident.id = profile.resident_id
                ORDER BY profile.risk_score DESC, profile.resident_id
                """
            ).fetchall(),
            "metadata_json",
        )


@router.get("/shocks")
def list_economic_shocks(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        return _decode(
            conn.execute(
                f"""
                SELECT shock.*, resident.name AS resident_name
                FROM economic_shocks shock
                JOIN residents resident ON resident.id = shock.resident_id
                ORDER BY shock.id DESC LIMIT {int(limit)}
                """
            ).fetchall(),
            "details_json",
        )


@router.get("/risk-claims")
def list_risk_pool_claims(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT claim.*, shock.shock_type
                FROM risk_pool_claims claim
                JOIN economic_shocks shock ON shock.id = claim.shock_id
                ORDER BY claim.id DESC LIMIT {int(limit)}
                """
            ).fetchall()
        ]
