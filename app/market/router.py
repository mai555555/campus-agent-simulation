import json

from fastapi import APIRouter, Query

from app.db import get_connection
from app.market.service import (
    evaluate_market_choice,
    find_market_mechanism,
    quote_market_offer,
)


router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/mechanisms")
def list_market_mechanisms():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(
            """
            SELECT mechanism.*, item.name AS item_name, item.item_type
            FROM market_mechanisms mechanism
            JOIN catalog_items item ON item.id = mechanism.item_id
            ORDER BY mechanism.location, item.name, mechanism.id
            """
        ).fetchall()]


@router.get("/prices")
def list_market_prices(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(
            f"""
            SELECT snapshot.*, mechanism.mechanism_key, item.name AS item_name,
                   mechanism.provider_actor_key, mechanism.location,
                   mechanism.pricing_mode
            FROM market_price_snapshots snapshot
            JOIN market_mechanisms mechanism ON mechanism.id = snapshot.mechanism_id
            JOIN catalog_items item ON item.id = mechanism.item_id
            ORDER BY snapshot.id DESC LIMIT {int(limit)}
            """
        ).fetchall()]


@router.get("/demand")
def list_market_demand(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(
            f"""
            SELECT signal.*, item.name AS item_name,
                   substitute.name AS substitute_item_name
            FROM market_demand_signals signal
            JOIN catalog_items item ON item.id = signal.item_id
            LEFT JOIN catalog_items substitute ON substitute.id = signal.substitute_item_id
            ORDER BY signal.id DESC LIMIT {int(limit)}
            """
        ).fetchall()]


@router.get("/frictions")
def list_market_frictions(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        result = []
        for row in conn.execute(
            f"""
            SELECT friction.*, mechanism.mechanism_key, item.name AS item_name
            FROM market_friction_events friction
            JOIN market_mechanisms mechanism ON mechanism.id = friction.mechanism_id
            JOIN catalog_items item ON item.id = mechanism.item_id
            ORDER BY friction.id DESC LIMIT {int(limit)}
            """
        ).fetchall():
            item = dict(row)
            item["details"] = json.loads(item.pop("details_json") or "{}")
            result.append(item)
        return result


@router.get("/quote")
def get_market_quote(
    item_name: str,
    location: str,
    resident_id: int | None = None,
):
    with get_connection() as conn:
        mechanism = find_market_mechanism(
            conn, item_name=item_name, location=location
        )
        if not mechanism:
            return {"available": False, "reason": "未找到匹配的市场"}
        if resident_id is None:
            return quote_market_offer(conn, int(mechanism["id"]))
        return evaluate_market_choice(
            conn,
            resident_id=resident_id,
            mechanism_id=int(mechanism["id"]),
        )
