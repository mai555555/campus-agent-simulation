import json

from fastapi import APIRouter, Query

from app.db import get_connection
from app.labor.service import income_distribution_summary


router = APIRouter(prefix="/api/labor", tags=["labor"])


@router.get("/distribution")
def get_income_distribution():
    with get_connection() as conn:
        return income_distribution_summary(conn)


@router.get("/positions")
def list_labor_positions():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT position.*, organization.name AS organization_name,
                   COUNT(contract.id) AS active_contracts
            FROM labor_positions position
            JOIN campus_organizations organization
              ON organization.id = position.organization_id
            LEFT JOIN employment_contracts contract
              ON contract.position_id = position.id
             AND contract.status = 'active'
            GROUP BY position.id, organization.id
            ORDER BY organization.id, position.id
            """
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["allowed_actions"] = json.loads(
                item.pop("allowed_actions_json") or "[]"
            )
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            item["active_contracts"] = int(item["active_contracts"])
            result.append(item)
        return result


@router.get("/contracts")
def list_employment_contracts(resident_id: int | None = None):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE contract.resident_id = ?", (resident_id,))
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT contract.*, resident.name AS resident_name,
                       position.title, position.location,
                       organization.name AS organization_name
                FROM employment_contracts contract
                JOIN residents resident ON resident.id = contract.resident_id
                JOIN labor_positions position ON position.id = contract.position_id
                JOIN campus_organizations organization
                  ON organization.id = position.organization_id
                {where}
                ORDER BY contract.id
                """,
                params,
            ).fetchall()
        ]


@router.get("/shifts")
def list_labor_shifts(
    resident_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE contract.resident_id = ?", (resident_id,))
        rows = conn.execute(
            f"""
            SELECT shift.*, contract.resident_id, resident.name AS resident_name,
                   position.title, organization.name AS organization_name
            FROM labor_shifts shift
            JOIN employment_contracts contract ON contract.id = shift.contract_id
            JOIN residents resident ON resident.id = contract.resident_id
            JOIN labor_positions position ON position.id = contract.position_id
            JOIN campus_organizations organization
              ON organization.id = position.organization_id
            {where}
            ORDER BY shift.id DESC LIMIT {int(limit)}
            """,
            params,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["evidence"] = json.loads(item.pop("evidence_json") or "[]")
            result.append(item)
        return result


@router.get("/income-programs")
def list_income_programs(resident_id: int | None = None):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE program.recipient_resident_id = ?", (resident_id,))
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT program.*, resident.name AS recipient_name
                FROM income_programs program
                JOIN residents resident
                  ON resident.id = program.recipient_resident_id
                {where}
                ORDER BY program.id
                """,
                params,
            ).fetchall()
        ]


@router.get("/payments")
def list_income_payments(
    resident_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = (
                "WHERE payment.recipient_actor_key = ?",
                (f"resident:{resident_id}",),
            )
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT payment.* FROM income_payments payment
                {where}
                ORDER BY payment.id DESC LIMIT {int(limit)}
                """,
                params,
            ).fetchall()
        ]


@router.get("/expense-obligations")
def list_expense_obligations(resident_id: int | None = None):
    with get_connection() as conn:
        where, params = ("", ())
        if resident_id is not None:
            where, params = ("WHERE obligation.resident_id = ?", (resident_id,))
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT obligation.*, resident.name AS resident_name
                FROM expense_obligations obligation
                JOIN residents resident ON resident.id = obligation.resident_id
                {where}
                ORDER BY obligation.resident_id, obligation.priority DESC
                """,
                params,
            ).fetchall()
        ]
