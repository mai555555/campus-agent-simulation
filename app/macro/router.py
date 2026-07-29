import json

from fastapi import APIRouter, HTTPException

from app.db import get_connection
from app.macro.service import build_macro_snapshot


router = APIRouter(prefix="/api/macro", tags=["macro"])


def _decode(row):
    item = dict(row)
    for key in ("metadata_json", "source_tables_json", "details_json"):
        if key in item:
            target = key[:-5]
            try:
                item[target] = json.loads(item.pop(key) or "{}")
            except (TypeError, ValueError):
                item[target] = {} if key != "source_tables_json" else []
    return item


@router.get("/definitions")
def list_metric_definitions():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM macro_metric_definitions ORDER BY category, id"
        ).fetchall()
        return [_decode(row) for row in rows]


@router.get("/snapshots")
def list_macro_snapshots(window_type: str | None = None, limit: int = 30):
    with get_connection() as conn:
        if window_type:
            rows = conn.execute(
                """
                SELECT * FROM macro_snapshots WHERE window_type = ?
                ORDER BY window_start DESC, id DESC LIMIT ?
                """,
                (window_type, min(max(limit, 1), 200)),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM macro_snapshots
                ORDER BY window_start DESC, id DESC LIMIT ?
                """,
                (min(max(limit, 1), 200),),
            ).fetchall()
        return [_decode(row) for row in rows]


@router.get("/snapshots/latest")
def get_latest_macro_snapshot(window_type: str = "daily"):
    with get_connection() as conn:
        snapshot = conn.execute(
            """
            SELECT * FROM macro_snapshots WHERE window_type = ?
            ORDER BY window_start DESC, id DESC LIMIT 1
            """,
            (window_type,),
        ).fetchone()
        if not snapshot:
            raise HTTPException(status_code=404, detail="宏观快照不存在")
        return _snapshot_detail(conn, int(snapshot["id"]))


@router.get("/snapshots/{snapshot_id}")
def get_macro_snapshot(snapshot_id: int):
    with get_connection() as conn:
        return _snapshot_detail(conn, snapshot_id)


def _snapshot_detail(conn, snapshot_id: int):
    snapshot = conn.execute(
        "SELECT * FROM macro_snapshots WHERE id = ?", (snapshot_id,)
    ).fetchone()
    if not snapshot:
        raise HTTPException(status_code=404, detail="宏观快照不存在")
    values = conn.execute(
        """
        SELECT value.*, definition.metric_key, definition.name,
               definition.category, definition.unit,
               definition.stock_flow_type, definition.aggregation_method
        FROM macro_metric_values value
        JOIN macro_metric_definitions definition
          ON definition.id = value.metric_definition_id
        WHERE value.snapshot_id = ?
        ORDER BY definition.category, definition.id, value.group_type, value.group_key
        """,
        (snapshot_id,),
    ).fetchall()
    checks = conn.execute(
        """
        SELECT * FROM macro_reconciliation_checks
        WHERE snapshot_id = ? ORDER BY severity DESC, id
        """,
        (snapshot_id,),
    ).fetchall()
    return {
        **_decode(snapshot),
        "values": [_decode(row) for row in values],
        "checks": [_decode(row) for row in checks],
    }


@router.get("/values/{metric_value_id}/components")
def list_metric_components(metric_value_id: int):
    with get_connection() as conn:
        value = conn.execute(
            """
            SELECT value.*, definition.metric_key, definition.name,
                   definition.unit, definition.aggregation_method
            FROM macro_metric_values value
            JOIN macro_metric_definitions definition
              ON definition.id = value.metric_definition_id
            WHERE value.id = ?
            """,
            (metric_value_id,),
        ).fetchone()
        if not value:
            raise HTTPException(status_code=404, detail="宏观指标值不存在")
        components = conn.execute(
            """
            SELECT * FROM macro_metric_components
            WHERE metric_value_id = ? ORDER BY id
            """,
            (metric_value_id,),
        ).fetchall()
        return {
            "value": _decode(value),
            "components": [_decode(row) for row in components],
        }


@router.post("/snapshots")
def create_macro_snapshot(window_type: str = "manual"):
    try:
        with get_connection() as conn:
            result = build_macro_snapshot(conn, window_type=window_type)
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
