from __future__ import annotations

from typing import Optional

import json

from fastapi import APIRouter, Query

from app.db import get_connection


router = APIRouter(prefix="/api/supply", tags=["supply"])


@router.get("/catalog")
def list_catalog_items():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM catalog_items ORDER BY item_type, name"
        ).fetchall()]


@router.get("/inventory")
def list_supply_inventory(owner_actor_key: Optional[str] = None):
    with get_connection() as conn:
        where, params = ("", ())
        if owner_actor_key:
            where, params = ("WHERE account.owner_actor_key = ?", (owner_actor_key,))
        return [dict(row) for row in conn.execute(
            f"""
            SELECT account.*, item.item_key, item.name, item.item_type,
                   item.shelf_life_hours, item.quality
            FROM inventory_accounts account
            JOIN catalog_items item ON item.id = account.item_id
            {where}
            ORDER BY account.owner_actor_key, item.name
            """,
            params,
        ).fetchall()]


@router.get("/production-batches")
def list_production_batches(
    status: Optional[str] = Query(default=None, pattern="^(running|completed|failed|cancelled)$"),
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where, params = ("", ())
        if status:
            where, params = ("WHERE batch.status = ?", (status,))
        rows = conn.execute(
            f"""
            SELECT batch.*, recipe.recipe_key, recipe.producer_actor_key,
                   item.name AS output_name
            FROM production_batches batch
            JOIN production_recipes recipe ON recipe.id = batch.recipe_id
            JOIN catalog_items item ON item.id = recipe.output_item_id
            {where}
            ORDER BY batch.id DESC LIMIT {int(limit)}
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/services")
def list_service_offerings():
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(
            """
            SELECT offering.*, item.name AS service_name
            FROM service_offerings offering
            JOIN catalog_items item ON item.id = offering.service_item_id
            ORDER BY offering.location, offering.id
            """
        ).fetchall()]


@router.get("/service-deliveries")
def list_service_deliveries(limit: int = Query(default=50, ge=1, le=200)):
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT delivery.*, offering.offering_key, item.name AS service_name
            FROM service_deliveries delivery
            JOIN service_offerings offering ON offering.id = delivery.offering_id
            JOIN catalog_items item ON item.id = offering.service_item_id
            ORDER BY delivery.id DESC LIMIT {int(limit)}
            """
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["result"] = json.loads(item.pop("result_json") or "{}")
            result.append(item)
        return result
