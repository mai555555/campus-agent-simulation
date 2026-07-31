from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.db import get_connection
from app.longitudinal.service import get_life_course


router = APIRouter(prefix="/api/longitudinal", tags=["longitudinal"])


@router.get("/residents/{resident_id}")
def resident_life_course(resident_id: int):
    with get_connection() as conn:
        result = get_life_course(conn, resident_id)
        if result is None:
            raise HTTPException(status_code=404, detail="居民长期轨迹不存在")
        return result


@router.get("/residents/{resident_id}/turning-points")
def resident_turning_points(resident_id: int, evidence_layer: Optional[str] = None):
    with get_connection() as conn:
        if evidence_layer:
            rows = conn.execute(
                """
                SELECT * FROM life_turning_points
                WHERE resident_id = ? AND evidence_layer = ?
                ORDER BY occurred_at DESC, id DESC
                """,
                (resident_id, evidence_layer),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM life_turning_points
                WHERE resident_id = ? ORDER BY occurred_at DESC, id DESC
                """,
                (resident_id,),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/residents/{resident_id}/path-dependencies")
def resident_path_dependencies(resident_id: int):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT * FROM path_dependency_links
                WHERE resident_id = ? ORDER BY occurred_at, id
                """,
                (resident_id,),
            ).fetchall()
        ]
