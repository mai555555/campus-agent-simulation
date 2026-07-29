from __future__ import annotations

from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import create_database_engine, get_connection
from app.spatial.planner import RouteNotFoundError
from app.spatial.repository import SpatialRepository
from app.spatial.runtime import (
    pause_spatial_movement,
    preview_route,
    resume_spatial_movement,
)
from app.spatial.schemas import (
    AgentSpatialStateResponse,
    AgentSpatialStatesResponse,
    AdmissionQueueResponse,
    MovementControlRequest,
    OccupancyResponse,
    RoutePlanRequest,
    SceneGraphResponse,
    SpatialResourcesResponse,
    TrajectoryResponse,
)
from app.spatial.service import (
    ResidentNotFoundError,
    SpatialService,
    SpatialStateNotInitializedError,
)


router = APIRouter(tags=["spatial"])


@lru_cache(maxsize=1)
def get_spatial_engine():
    return create_database_engine()


def with_spatial_service(callback):
    engine = get_spatial_engine()
    with engine.connect() as connection:
        return callback(SpatialService(SpatialRepository(connection)))


@router.get("/api/spatial/scene", response_model=SceneGraphResponse)
def get_spatial_scene():
    return with_spatial_service(lambda service: service.get_scene_graph())


@router.get("/api/spatial/occupancy", response_model=OccupancyResponse)
def get_spatial_occupancy():
    return with_spatial_service(lambda service: service.get_occupancy())


@router.get("/api/spatial/resources", response_model=SpatialResourcesResponse)
def get_spatial_resources():
    return with_spatial_service(lambda service: service.get_resources())


@router.get("/api/spatial/admission-queue", response_model=AdmissionQueueResponse)
def get_spatial_admission_queue():
    return with_spatial_service(lambda service: service.get_admission_queue())


@router.get("/api/spatial/agents", response_model=AgentSpatialStatesResponse)
def get_spatial_agents():
    return with_spatial_service(lambda service: service.list_agent_states())


@router.get(
    "/api/agents/{resident_id}/spatial-state",
    response_model=AgentSpatialStateResponse,
)
def get_agent_spatial_state(resident_id: int):
    try:
        return with_spatial_service(
            lambda service: service.get_agent_state(resident_id)
        )
    except ResidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SpatialStateNotInitializedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/api/agents/{resident_id}/trajectory",
    response_model=TrajectoryResponse,
)
def get_agent_trajectory(
    resident_id: int,
    run_id: Optional[int] = Query(default=None, ge=1),
    branch_key: str = Query(default="main", min_length=1, max_length=80),
    from_tick: Optional[int] = Query(default=None, ge=0),
    to_tick: Optional[int] = Query(default=None, ge=0),
):
    try:
        return with_spatial_service(
            lambda service: service.get_trajectory(
                resident_id,
                experiment_run_id=run_id,
                branch_key=branch_key,
                from_tick=from_tick,
                to_tick=to_tick,
            )
        )
    except ResidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/api/agents/{resident_id}/movement/plan")
def plan_agent_movement(resident_id: int, payload: RoutePlanRequest):
    try:
        with get_connection() as connection:
            return preview_route(connection, resident_id, payload.destination)
    except RouteNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/agents/{resident_id}/movement/pause")
def pause_agent_movement(resident_id: int, payload: MovementControlRequest):
    try:
        with get_connection() as connection:
            result = pause_spatial_movement(
                connection,
                resident_id,
                reason=payload.reason,
            )
            connection.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/agents/{resident_id}/movement/resume")
def resume_agent_movement(resident_id: int):
    try:
        with get_connection() as connection:
            result = resume_spatial_movement(connection, resident_id)
            connection.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
