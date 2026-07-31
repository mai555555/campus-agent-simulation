from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.db import get_connection
from app.economy.service import MINOR_PER_COIN, reconcile_ledger


router = APIRouter(prefix="/api/economy", tags=["economy"])


@router.get("/actors")
def list_economic_actors():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ea.*,
                   COUNT(la.id) AS account_count,
                   COALESCE(SUM(
                       CASE WHEN la.account_code = 'cash'
                            THEN la.balance_minor ELSE 0 END
                   ), 0) AS cash_minor
            FROM economic_actors ea
            LEFT JOIN ledger_accounts la ON la.actor_id = ea.id
            GROUP BY ea.id
            ORDER BY ea.actor_type, ea.id
            """
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "actor_key": row["actor_key"],
                "actor_type": row["actor_type"],
                "display_name": row["display_name"],
                "resident_id": row["resident_id"],
                "organization_id": row["organization_id"],
                "status": row["status"],
                "account_count": int(row["account_count"]),
                "cash_balance": int(row["cash_minor"]) / MINOR_PER_COIN,
            }
            for row in rows
        ]


@router.get("/accounts")
def list_ledger_accounts(actor_key: Optional[str] = None):
    with get_connection() as conn:
        params = ()
        where = ""
        if actor_key:
            where = "WHERE ea.actor_key = ?"
            params = (actor_key,)
        rows = conn.execute(
            f"""
            SELECT la.*, ea.actor_key, ea.display_name
            FROM ledger_accounts la
            JOIN economic_actors ea ON ea.id = la.actor_id
            {where}
            ORDER BY ea.id, la.id
            """,
            params,
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "account_key": row["account_key"],
                "account_code": row["account_code"],
                "actor_key": row["actor_key"],
                "actor_name": row["display_name"],
                "account_type": row["account_type"],
                "normal_side": row["normal_side"],
                "currency": row["currency"],
                "balance_minor": int(row["balance_minor"]),
                "balance": int(row["balance_minor"]) / MINOR_PER_COIN,
                "status": row["status"],
            }
            for row in rows
        ]


@router.get("/transactions")
def list_ledger_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    before_id: Optional[int] = Query(default=None, ge=1),
):
    with get_connection() as conn:
        where = ""
        params: tuple = ()
        if before_id is not None:
            where = "WHERE lt.id < ?"
            params = (before_id,)
        transactions = conn.execute(
            f"""
            SELECT lt.*
            FROM ledger_transactions lt
            {where}
            ORDER BY lt.id DESC
            LIMIT {int(limit)}
            """,
            params,
        ).fetchall()
        result = []
        for transaction in transactions:
            entries = conn.execute(
                """
                SELECT le.*, la.account_key, ea.actor_key, ea.display_name
                FROM ledger_entries le
                JOIN ledger_accounts la ON la.id = le.account_id
                JOIN economic_actors ea ON ea.id = la.actor_id
                WHERE le.transaction_id = ?
                ORDER BY le.id
                """,
                (transaction["id"],),
            ).fetchall()
            result.append(
                {
                    "id": int(transaction["id"]),
                    "transaction_key": transaction["transaction_key"],
                    "transaction_type": transaction["transaction_type"],
                    "status": transaction["status"],
                    "source_type": transaction["source_type"],
                    "source_id": transaction["source_id"],
                    "action_execution_id": transaction["action_execution_id"],
                    "world_event_id": transaction["world_event_id"],
                    "occurred_at": transaction["occurred_at"],
                    "rule_version": transaction["rule_version"],
                    "description": transaction["description"],
                    "entries": [
                        {
                            "account_key": entry["account_key"],
                            "actor_key": entry["actor_key"],
                            "actor_name": entry["display_name"],
                            "entry_side": entry["entry_side"],
                            "amount_minor": int(entry["amount_minor"]),
                            "amount": int(entry["amount_minor"]) / MINOR_PER_COIN,
                            "currency": entry["currency"],
                            "memo": entry["memo"],
                        }
                        for entry in entries
                    ],
                }
            )
        return result


@router.get("/reconciliation")
def get_ledger_reconciliation():
    with get_connection() as conn:
        return reconcile_ledger(conn)


@router.get("/authorization-rules")
def list_ledger_authorization_rules():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT rule_key, operation_type, authority_actor_key,
                   counterparty_account_key, counterparty_side,
                   max_amount_minor, allowed_target_actor_types,
                   status, rule_version
            FROM ledger_authorization_rules
            ORDER BY operation_type, id
            """
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/audit-events")
def list_ledger_audit_events(
    status: Optional[str] = Query(default=None, pattern="^(open|resolved)$"),
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where = ""
        params: tuple = ()
        if status:
            where = "WHERE status = ?"
            params = (status,)
        rows = conn.execute(
            f"""
            SELECT * FROM ledger_audit_events
            {where}
            ORDER BY id DESC
            LIMIT {int(limit)}
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]
