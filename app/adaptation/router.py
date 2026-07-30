import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.adaptation.institutions import (
    record_rule_deliberation,
    submit_rule_proposal,
)
from app.adaptation.service import list_constraint_evaluations
from app.db import get_connection


router = APIRouter(prefix="/api/adaptation", tags=["adaptation"])


class RuleProposalRequest(BaseModel):
    proposal_key: str = Field(min_length=1, max_length=160)
    organization_id: int
    proposer_resident_id: int
    primitive_key: str
    title: str
    rationale: str
    scope_type: str
    scope_key: str
    parameters: dict
    source_norm_id: int | None = None
    requested_budget_minor: int = Field(default=0, ge=0)
    monitoring_plan: dict = Field(default_factory=dict)
    review_after_days: int = Field(default=30, ge=1)
    repeal_conditions: dict = Field(default_factory=dict)


class RuleDeliberationRequest(BaseModel):
    participant_type: str
    participant_id: str
    stance: str
    argument: str
    influence_weight: float = Field(default=1, gt=0)
    evidence: dict = Field(default_factory=dict)


def _decode_attempt(row):
    item = dict(row)
    try:
        item["outcome"] = json.loads(item.pop("outcome_json") or "{}")
    except (TypeError, ValueError):
        item["outcome"] = {}
    return item


@router.get("/constraint-rules")
def get_constraint_rules():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM constraint_rules ORDER BY constraint_layer, id"
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/constraint-evaluations")
def get_constraint_evaluations(resident_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        return list_constraint_evaluations(conn, resident_id, limit)


@router.get("/boundary-attempts")
def get_boundary_attempts(resident_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        if resident_id is None:
            rows = conn.execute(
                "SELECT * FROM boundary_attempts ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM boundary_attempts WHERE resident_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (resident_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [_decode_attempt(row) for row in rows]


@router.get("/constraint-consequences")
def get_constraint_consequences(attempt_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        if attempt_id is None:
            rows = conn.execute(
                "SELECT * FROM constraint_consequences ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM constraint_consequences WHERE attempt_id = ?
                ORDER BY id LIMIT ?
                """,
                (attempt_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/memories")
def get_adaptive_memories(resident_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        params = []
        where = ""
        if resident_id is not None:
            where = "WHERE memory.resident_id = ?"
            params.append(resident_id)
        params.append(min(max(limit, 1), 500))
        rows = conn.execute(
            f"""
            SELECT memory.*, experience.event_type,
                   experience.objective_summary, experience.branch_key,
                   experience.occurred_at
            FROM adaptive_memories memory
            JOIN experience_records experience ON experience.id = memory.experience_id
            {where}
            ORDER BY memory.id DESC LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/strategies")
def get_strategy_states(resident_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        if resident_id is None:
            rows = conn.execute(
                "SELECT * FROM strategy_states ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM strategy_states WHERE resident_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (resident_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/learning-updates")
def get_learning_updates(resident_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        if resident_id is None:
            rows = conn.execute(
                "SELECT * FROM learning_updates ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM learning_updates WHERE resident_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (resident_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/norms")
def get_norm_candidates(state: str | None = None, limit: int = 100):
    with get_connection() as conn:
        if state is None:
            rows = conn.execute(
                "SELECT * FROM norm_candidates ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM norm_candidates WHERE state = ?
                ORDER BY id DESC LIMIT ?
                """,
                (state, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/norm-signals")
def get_norm_signals(behavior_key: str | None = None, limit: int = 100):
    with get_connection() as conn:
        if behavior_key is None:
            rows = conn.execute(
                "SELECT * FROM norm_signals ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM norm_signals WHERE behavior_key = ?
                ORDER BY id DESC LIMIT ?
                """,
                (behavior_key, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/norms/{norm_id}/evidence")
def get_norm_evidence(norm_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT evidence.*, signal.behavior_key, signal.signal_type,
                   signal.source_type, signal.source_id, signal.details_json
            FROM norm_evidence evidence
            JOIN norm_signals signal ON signal.id = evidence.signal_id
            WHERE evidence.norm_id = ? ORDER BY evidence.id
            """,
            (norm_id,),
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/norm-beliefs")
def get_norm_beliefs(resident_id: int | None = None, limit: int = 100):
    with get_connection() as conn:
        if resident_id is None:
            rows = conn.execute(
                "SELECT * FROM agent_norm_beliefs ORDER BY last_updated_at DESC LIMIT ?",
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM agent_norm_beliefs WHERE resident_id = ?
                ORDER BY last_updated_at DESC LIMIT ?
                """,
                (resident_id, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.get("/rule-primitives")
def get_rule_primitives():
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM rule_primitives ORDER BY rule_layer, id"
            ).fetchall()
        ]


@router.get("/rule-proposals")
def get_rule_proposals(status: str | None = None, limit: int = 100):
    with get_connection() as conn:
        if status is None:
            rows = conn.execute(
                """
                SELECT * FROM institutional_rule_proposals
                ORDER BY id DESC LIMIT ?
                """,
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM institutional_rule_proposals WHERE status = ?
                ORDER BY id DESC LIMIT ?
                """,
                (status, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]


@router.post("/rule-proposals")
def create_rule_proposal(payload: RuleProposalRequest):
    try:
        with get_connection() as conn:
            result = submit_rule_proposal(conn, **payload.model_dump())
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/rule-proposals/{proposal_id}/deliberations")
def create_rule_deliberation(
    proposal_id: int, payload: RuleDeliberationRequest
):
    try:
        with get_connection() as conn:
            result = record_rule_deliberation(
                conn, proposal_id=proposal_id, **payload.model_dump()
            )
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/rule-versions")
def get_rule_versions(lineage_key: str | None = None, limit: int = 100):
    with get_connection() as conn:
        if lineage_key is None:
            rows = conn.execute(
                """
                SELECT * FROM evolved_rule_versions
                ORDER BY effective_from DESC, id DESC LIMIT ?
                """,
                (min(max(limit, 1), 500),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM evolved_rule_versions WHERE lineage_key = ?
                ORDER BY version DESC LIMIT ?
                """,
                (lineage_key, min(max(limit, 1), 500)),
            ).fetchall()
        return [dict(row) for row in rows]
