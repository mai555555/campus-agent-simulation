import json

from fastapi import APIRouter, Query

from app.db import get_connection
from app.organizations.service import organization_budget_state


router = APIRouter(prefix="/api/organization-runtime", tags=["organizations"])


@router.get("/organizations")
def list_runtime_organizations():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT organization.id, organization.name,
                   organization.organization_type, organization.goal,
                   organization.status, profile.governance_mode,
                   profile.mission, profile.reputation,
                   profile.decision_delay_minutes, profile.quorum_weight,
                   COUNT(DISTINCT assignment.resident_id) AS active_members
            FROM campus_organizations organization
            JOIN organization_runtime_profiles profile
              ON profile.organization_id = organization.id
            LEFT JOIN organization_role_assignments assignment
              ON assignment.organization_id = organization.id
             AND assignment.status = 'active'
            GROUP BY organization.id, profile.organization_id
            ORDER BY organization.organization_type, organization.id
            """
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["budget"] = organization_budget_state(conn, int(row["id"]))
            item["active_members"] = int(item["active_members"])
            result.append(item)
        return result


@router.get("/organizations/{organization_id}")
def get_runtime_organization(organization_id: int):
    with get_connection() as conn:
        organization = conn.execute(
            """
            SELECT organization.*, profile.governance_mode, profile.mission,
                   profile.reputation, profile.decision_delay_minutes,
                   profile.quorum_weight, profile.metadata_json
            FROM campus_organizations organization
            JOIN organization_runtime_profiles profile
              ON profile.organization_id = organization.id
            WHERE organization.id = ?
            """,
            (organization_id,),
        ).fetchone()
        if not organization:
            return {"organization": None}
        roles = conn.execute(
            """
            SELECT role.*, assignment.resident_id, resident.name AS resident_name
            FROM organization_roles role
            LEFT JOIN organization_role_assignments assignment
              ON assignment.role_id = role.id AND assignment.status = 'active'
            LEFT JOIN residents resident ON resident.id = assignment.resident_id
            WHERE role.organization_id = ?
            ORDER BY role.id, resident.id
            """,
            (organization_id,),
        ).fetchall()
        relationships = conn.execute(
            """
            SELECT relation.*, target.name AS target_name
            FROM organization_relationships relation
            JOIN campus_organizations target
              ON target.id = relation.to_organization_id
            WHERE relation.from_organization_id = ?
            ORDER BY target.id
            """,
            (organization_id,),
        ).fetchall()
        item = dict(organization)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        item["budget"] = organization_budget_state(conn, organization_id)
        item["roles"] = []
        for role in roles:
            value = dict(role)
            value["permissions"] = json.loads(value.pop("permissions_json") or "[]")
            item["roles"].append(value)
        item["relationships"] = [dict(row) for row in relationships]
        return {"organization": item}


@router.get("/proposals")
def list_organization_proposals(
    organization_id: int | None = None,
    status: str | None = Query(
        default=None,
        pattern="^(pending|approved|rejected|executed|cancelled|expired)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        clauses = []
        params: list = []
        if organization_id is not None:
            clauses.append("proposal.organization_id = ?")
            params.append(organization_id)
        if status:
            clauses.append("proposal.status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"""
            SELECT proposal.*, organization.name AS organization_name,
                   proposer.name AS proposer_name
            FROM organization_proposals proposal
            JOIN campus_organizations organization
              ON organization.id = proposal.organization_id
            JOIN residents proposer ON proposer.id = proposal.proposer_resident_id
            {where}
            ORDER BY proposal.id DESC
            LIMIT {int(limit)}
            """,
            tuple(params),
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/commitments")
def list_organization_commitments(
    organization_id: int | None = None,
    status: str | None = Query(
        default=None,
        pattern="^(active|fulfilled|breached|cancelled)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        clauses = []
        params: list = []
        if organization_id is not None:
            clauses.append("commitment.organization_id = ?")
            params.append(organization_id)
        if status:
            clauses.append("commitment.status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"""
            SELECT commitment.*, organization.name AS organization_name,
                   resident.name AS responsible_name
            FROM organization_commitments commitment
            JOIN campus_organizations organization
              ON organization.id = commitment.organization_id
            LEFT JOIN residents resident
              ON resident.id = commitment.responsibility_resident_id
            {where}
            ORDER BY commitment.id DESC
            LIMIT {int(limit)}
            """,
            tuple(params),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            result.append(item)
        return result


@router.get("/events")
def list_organization_events(
    organization_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    with get_connection() as conn:
        where = ""
        params: tuple = ()
        if organization_id is not None:
            where = "WHERE event.organization_id = ?"
            params = (organization_id,)
        rows = conn.execute(
            f"""
            SELECT event.*, organization.name AS organization_name
            FROM organization_events event
            JOIN campus_organizations organization
              ON organization.id = event.organization_id
            {where}
            ORDER BY event.id DESC
            LIMIT {int(limit)}
            """,
            params,
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["details"] = json.loads(item.pop("details_json") or "{}")
            result.append(item)
        return result

