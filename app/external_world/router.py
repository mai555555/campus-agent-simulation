from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection
from app.external_world.service import (
    begin_sync_run,
    bind_external_experiment,
    configure_external_mode,
    create_external_snapshot,
    export_external_snapshot,
    ingest_raw_observation,
    normalize_external_event,
    propose_event_impacts,
    register_source,
    review_external_source,
    schedule_exposure,
    sync_registered_source,
)


router = APIRouter(prefix="/api/external", tags=["external-world"])


def _require_admin(role):
    if role != "admin":
        raise HTTPException(status_code=403, detail="该操作需要 admin 权限")


class SourceRequest(BaseModel):
    source_key: str
    name: str
    source_type: str
    adapter_key: str
    base_url: str = ""
    trust_prior: float = Field(default=0.5, ge=0, le=1)
    allowed_event_types: list[str] = Field(default_factory=list)
    poll_interval_seconds: int = Field(default=3600, ge=1)
    stale_after_seconds: int = Field(default=7200, ge=1)
    license_note: str = ""
    allowed_use: str = "simulation"
    retention_days: int = Field(default=30, ge=0)
    sensitivity: str = "public"
    config: dict = Field(default_factory=dict)


class RawObservationRequest(BaseModel):
    source_record_id: str
    payload: dict
    observed_at: str
    parser_version: str
    sync_run_id: Optional[int] = None
    request_fingerprint: str = ""
    http_status: int = 200
    content_type: str = "application/json"
    ingested_at: Optional[str] = None


class NormalizeEventRequest(BaseModel):
    raw_observation_id: int
    event_key: str
    event_type: str
    title: str
    summary: str
    occurred_at: str
    published_at: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    expires_at: Optional[str] = None
    geo_scope: dict = Field(default_factory=dict)
    campus_scope: dict = Field(default_factory=dict)
    affected_spaces: list[str] = Field(default_factory=list)
    affected_roles: list[str] = Field(default_factory=list)
    affected_organizations: list[str] = Field(default_factory=list)
    affected_economic_sectors: list[str] = Field(default_factory=list)
    magnitude: Optional[float] = None
    direction: str = "neutral"
    unit: str = ""
    severity: float = Field(default=0, ge=0, le=1)
    novelty: float = Field(default=0, ge=0, le=1)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    verification_state: str = "unverified"
    payload: dict = Field(default_factory=dict)
    semantic_key: str = ""
    correction_of: Optional[int] = None
    replaces_event_id: Optional[int] = None


class SnapshotRequest(BaseModel):
    snapshot_key: str
    window_start: str
    window_end: str
    mode: str = "snapshot"
    metadata: dict = Field(default_factory=dict)
    seal: bool = True


class ModeRequest(BaseModel):
    branch_key: str = "main"
    mode: str
    snapshot_id: Optional[int] = None
    replay_start_world_time: Optional[str] = None
    replay_speed: float = Field(default=1, gt=0)
    simulation_seed: int = 0


class ExposureRequest(BaseModel):
    exposure_key: str
    external_event_id: int
    resident_id: int
    channel: str
    scheduled_at: str
    credibility_at_delivery: float = Field(ge=0, le=1)
    sender_resident_id: Optional[int] = None
    parent_exposure_id: Optional[int] = None
    distortion: dict = Field(default_factory=dict)
    attention_cost: float = Field(default=0, ge=0)
    correction_of_exposure_id: Optional[int] = None


class GovernanceReviewRequest(BaseModel):
    reviewer: str
    decision: str
    reviewed_at: Optional[str] = None
    license_approved: bool = False
    purpose_approved: bool = False
    retention_approved: bool = False
    privacy_approved: bool = False
    notes: str = ""


class ExperimentBindingRequest(BaseModel):
    experiment_key: str
    branch_key: str = "main"
    external_mode: str
    simulation_seed: int
    snapshot_id: Optional[int] = None
    metadata: dict = Field(default_factory=dict)


class SnapshotExportRequest(BaseModel):
    export_key: str
    requested_by: str


@router.get("/sources")
def list_sources():
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, source_key, name, source_type, base_url, adapter_key,
                       enabled, trust_prior, license_note, allowed_use,
                       sensitivity, last_success_at, status
                FROM external_sources ORDER BY id
                """
            ).fetchall()
        ]


@router.post("/sources")
def create_source(payload: SourceRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = register_source(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/sources/{source_id}/sync-runs")
def create_sync_run(source_id: int, run_key: str, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    with get_connection() as conn:
        result = begin_sync_run(conn, source_id, run_key)
        conn.commit()
        return result


@router.post("/sources/{source_id}/sync")
def sync_source(source_id: int, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = sync_registered_source(conn, source_id)
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"外部来源同步失败：{type(exc).__name__}",
        ) from exc


@router.post("/sources/{source_id}/observations")
def create_raw_observation(source_id: int, payload: RawObservationRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = ingest_raw_observation(conn, source_id=source_id, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/sync-runs")
def list_sync_runs(limit: int = 100):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM external_sync_runs ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        ]


@router.post("/events")
def create_normalized_event(payload: NormalizeEventRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = normalize_external_event(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/events")
def list_events(limit: int = 100):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM external_events ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        ]


@router.get("/events/{event_id}")
def get_event(event_id: int):
    with get_connection() as conn:
        event = conn.execute(
            "SELECT * FROM external_events WHERE id = ?", (event_id,)
        ).fetchone()
        if not event:
            raise HTTPException(status_code=404, detail="外部事件不存在")
        return dict(event)


@router.get("/events/{event_id}/provenance")
def get_event_provenance(event_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT event.*, source.source_key, source.name AS source_name,
                   source.license_note, raw.content_hash, raw.payload_json,
                   raw.parser_version, raw.validation_status
            FROM external_events event
            JOIN external_sources source ON source.id = event.source_id
            JOIN external_raw_observations raw ON raw.id = event.raw_observation_id
            WHERE event.id = ?
            """,
            (event_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="外部事件不存在")
        return dict(row)


@router.get("/events/{event_id}/impacts")
def get_event_impacts(event_id: int):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT * FROM external_event_impacts
                WHERE external_event_id = ? ORDER BY id
                """,
                (event_id,),
            ).fetchall()
        ]


@router.post("/events/{event_id}/impacts")
def create_event_impacts(event_id: int, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    with get_connection() as conn:
        result = propose_event_impacts(conn, event_id)
        conn.commit()
        return result


@router.get("/events/{event_id}/exposures")
def get_event_exposures(event_id: int):
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT * FROM external_exposures
                WHERE external_event_id = ? ORDER BY id
                """,
                (event_id,),
            ).fetchall()
        ]


@router.post("/exposures")
def create_exposure(payload: ExposureRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    with get_connection() as conn:
        result = schedule_exposure(conn, **payload.model_dump())
        conn.commit()
        return result


@router.post("/snapshots")
def create_snapshot(payload: SnapshotRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    with get_connection() as conn:
        result = create_external_snapshot(conn, **payload.model_dump())
        conn.commit()
        return result


@router.get("/snapshots")
def list_snapshots():
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM external_data_snapshots ORDER BY id DESC"
            ).fetchall()
        ]


@router.post("/modes")
def set_external_mode(payload: ModeRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = configure_external_mode(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/health")
def get_external_health(branch_key: str = "main"):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM external_runtime_health WHERE branch_key = ?",
            (branch_key,),
        ).fetchone()
        return dict(row) if row else {"branch_key": branch_key, "status": "unknown"}


@router.post("/sources/{source_id}/reviews")
def review_source(source_id: int, payload: GovernanceReviewRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = review_external_source(
                conn, source_id=source_id, **payload.model_dump()
            )
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/experiments")
def bind_experiment(payload: ExperimentBindingRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = bind_external_experiment(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/snapshots/{snapshot_id}/exports")
def export_snapshot(snapshot_id: int, payload: SnapshotExportRequest, x_external_role: str = Header(default="observer")):
    _require_admin(x_external_role)
    try:
        with get_connection() as conn:
            result = export_external_snapshot(
                conn, snapshot_id=snapshot_id, **payload.model_dump()
            )
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
