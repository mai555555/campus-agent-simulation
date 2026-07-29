from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import get_connection
from app.perception_runtime import (
    get_agent_cognitive_context,
    perception_runtime_available,
)
from app.perception_schemas import (
    AgentPerceptionEvidenceResponse,
    ObservationResearchResponse,
)


router = APIRouter(tags=["perception"])


@router.get(
    "/api/agents/{resident_id}/perception-evidence",
    response_model=AgentPerceptionEvidenceResponse,
)
def get_agent_perception_evidence(
    resident_id: int,
    limit: int = Query(default=20, ge=1, le=100),
):
    with get_connection() as conn:
        resident = conn.execute(
            "SELECT id FROM residents WHERE id = ?",
            (resident_id,),
        ).fetchone()
        if not resident:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        if not perception_runtime_available(conn):
            raise HTTPException(status_code=409, detail="局部感知运行时尚未初始化")
        branch = conn.execute(
            "SELECT active_branch_key FROM world_runtime WHERE id = 1"
        ).fetchone()
        context = get_agent_cognitive_context(
            conn,
            resident_id,
            branch_key=branch["active_branch_key"] if branch else "main",
            limit=limit,
        )
        return {
            "resident_id": resident_id,
            "information_boundary": (
                "观察是局部证据，信念是 Agent 的当前解释，空间记忆是带地点的主观经历；"
                "均不等同于世界完整真相。"
            ),
            **context,
        }


@router.get(
    "/api/perception/observations",
    response_model=ObservationResearchResponse,
)
def list_observations(
    resident_id: Optional[int] = Query(default=None, ge=1),
    tick_id: Optional[int] = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
):
    clauses = []
    params = []
    if resident_id is not None:
        clauses.append("observation.observer_resident_id = ?")
        params.append(resident_id)
    if tick_id is not None:
        clauses.append("observation.tick_id = ?")
        params.append(tick_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    with get_connection() as conn:
        if not perception_runtime_available(conn):
            return {"observations": []}
        rows = conn.execute(
            f"""
            SELECT observation.*, resident.name AS observer_name,
                   node.name AS origin_node_name
            FROM agent_observations observation
            JOIN residents resident
              ON resident.id = observation.observer_resident_id
            LEFT JOIN spatial_nodes node ON node.id = observation.origin_node_id
            {where}
            ORDER BY observation.id DESC LIMIT ?
            """,
            params,
        ).fetchall()
        return {"observations": [dict(row) for row in rows]}
