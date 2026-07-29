from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.body_runtime import body_runtime_available
from app.body_schemas import AgentBodyStateResponse, AgentBodyStatesResponse
from app.db import get_connection


router = APIRouter(tags=["body"])


def _alerts(state):
    alerts = []
    if float(state["fatigue"]) >= 75:
        alerts.append("疲劳")
    if float(state["hunger"]) >= 80:
        alerts.append("饥饿")
    if float(state["stress"]) >= 75:
        alerts.append("高压力")
    if float(state["attention"]) <= 25:
        alerts.append("注意力不足")
    if float(state["health"]) <= 55:
        alerts.append("健康风险")
    return alerts


def _body_rows(conn, resident_id=None):
    where = "WHERE body.resident_id = ?" if resident_id is not None else ""
    params = (resident_id,) if resident_id is not None else ()
    rows = conn.execute(
        f"""
        SELECT body.*, residents.name AS resident_name, residents.role,
               residents.location
        FROM agent_body_states body
        JOIN residents ON residents.id = body.resident_id
        {where}
        ORDER BY body.resident_id
        """,
        params,
    ).fetchall()
    return [{**dict(row), "alerts": _alerts(row)} for row in rows]


@router.get("/api/body-states", response_model=AgentBodyStatesResponse)
def list_body_states():
    with get_connection() as conn:
        if not body_runtime_available(conn):
            return {"agents": []}
        return {"agents": _body_rows(conn)}


@router.get(
    "/api/agents/{resident_id}/body-state",
    response_model=AgentBodyStateResponse,
)
def get_agent_body_state(resident_id: int):
    with get_connection() as conn:
        if not body_runtime_available(conn):
            raise HTTPException(status_code=409, detail="身体状态运行时尚未初始化")
        rows = _body_rows(conn, resident_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Agent 身体状态不存在")
        return rows[0]
