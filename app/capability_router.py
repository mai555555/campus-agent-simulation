from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.capability_runtime import (
    capability_runtime_available,
    get_capability_profile,
    get_opportunity_access,
)
from app.capability_schemas import (
    CapabilityProfileResponse,
    CapabilityResearchResponse,
)
from app.db import get_connection


router = APIRouter(tags=["capability"])


@router.get(
    "/api/agents/{resident_id}/capability-profile",
    response_model=CapabilityProfileResponse,
)
def get_agent_capability_profile(resident_id: int):
    with get_connection() as conn:
        resident = conn.execute(
            "SELECT id FROM residents WHERE id = ?",
            (resident_id,),
        ).fetchone()
        if not resident:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        if not capability_runtime_available(conn):
            raise HTTPException(status_code=409, detail="能力运行时尚未初始化")
        profile = get_capability_profile(conn, resident_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Agent 能力档案不存在")
        spatial = conn.execute(
            """
            SELECT base_speed_m_per_min, mobility_class, perception_radius_m,
                   hearing_radius_m, source, version
            FROM agent_spatial_capabilities WHERE resident_id = ?
            """,
            (resident_id,),
        ).fetchone()
        return {
            "resident_id": resident_id,
            "capability_profile": profile,
            "opportunities": get_opportunity_access(conn, resident_id),
            "spatial_capability": dict(spatial) if spatial else None,
            "interpretation_boundary": (
                "这些数值是仿真中的结构化行动参数，用于解释成本、可达性与信息差异；"
                "不是人物介绍，也不代表现实中的固定能力评价。"
            ),
        }


@router.get(
    "/api/capabilities",
    response_model=CapabilityResearchResponse,
)
def list_capability_profiles(limit: int = Query(default=100, ge=1, le=500)):
    with get_connection() as conn:
        if not capability_runtime_available(conn):
            return {"profiles": []}
        rows = conn.execute(
            """
            SELECT profile.*, resident.name, resident.role
            FROM agent_capability_profiles profile
            JOIN residents resident ON resident.id = profile.resident_id
            ORDER BY profile.resident_id LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {"profiles": [dict(row) for row in rows]}

