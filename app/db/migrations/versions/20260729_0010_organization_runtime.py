"""Add governed organization runtime and collective action records.

Revision ID: 20260729_0010
Revises: 20260729_0009
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0010"
down_revision = "20260729_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_runtime_profiles",
        sa.Column("organization_id", sa.Integer(), primary_key=True),
        sa.Column("governance_mode", sa.String(24), nullable=False, server_default="council"),
        sa.Column("mission", sa.Text(), nullable=False, server_default=""),
        sa.Column("reputation", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("decision_delay_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("quorum_weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="CASCADE"),
        sa.CheckConstraint("governance_mode IN ('executive', 'council', 'consensus')", name="ck_organization_profiles_governance_valid"),
        sa.CheckConstraint("reputation BETWEEN 0 AND 100", name="ck_organization_profiles_reputation_valid"),
        sa.CheckConstraint("decision_delay_minutes >= 0", name="ck_organization_profiles_delay_nonnegative"),
        sa.CheckConstraint("quorum_weight > 0", name="ck_organization_profiles_quorum_positive"),
    )
    op.create_table(
        "organization_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("role_key", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("permissions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("spending_limit_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("vote_weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "role_key", name="uq_organization_roles_org_key"),
        sa.CheckConstraint("spending_limit_minor >= 0", name="ck_organization_roles_limit_nonnegative"),
        sa.CheckConstraint("vote_weight > 0", name="ck_organization_roles_vote_positive"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_organization_roles_status_valid"),
    )
    op.create_index("ix_organization_roles_org_status", "organization_roles", ["organization_id", "status"])
    op.create_table(
        "organization_role_assignments",
        sa.Column("organization_id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("assigned_by_resident_id", sa.Integer()),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["organization_roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by_resident_id"], ["residents.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_organization_assignments_status_valid"),
    )
    op.create_table(
        "organization_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proposal_key", sa.String(200), nullable=False, unique=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("proposer_resident_id", sa.Integer(), nullable=False),
        sa.Column("proposal_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("requested_budget_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("target_actor_key", sa.String(120), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("approvals_required", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approvals_weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejections_weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("earliest_decision_at", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("decision_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("ledger_transaction_id", sa.Integer()),
        sa.Column("source_type", sa.String(64), nullable=False, server_default="organization_runtime"),
        sa.Column("source_id", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("executed_at", sa.String(64), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposer_resident_id"], ["residents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL"),
        sa.CheckConstraint("requested_budget_minor >= 0", name="ck_organization_proposals_budget_nonnegative"),
        sa.CheckConstraint("approvals_required > 0", name="ck_organization_proposals_approvals_positive"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'executed', 'cancelled', 'expired')", name="ck_organization_proposals_status_valid"),
    )
    op.create_index("ix_organization_proposals_due", "organization_proposals", ["status", "earliest_decision_at", "id"])
    op.create_table(
        "organization_votes",
        sa.Column("proposal_id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("vote_weight", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["proposal_id"], ["organization_proposals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("decision IN ('approve', 'reject')", name="ck_organization_votes_decision_valid"),
        sa.CheckConstraint("vote_weight > 0", name="ck_organization_votes_weight_positive"),
    )
    op.create_table(
        "organization_commitments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commitment_key", sa.String(200), nullable=False, unique=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer()),
        sa.Column("commitment_type", sa.String(64), nullable=False),
        sa.Column("counterparty_actor_key", sa.String(120), nullable=False, server_default=""),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("due_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("responsibility_resident_id", sa.Integer()),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.String(64), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposal_id"], ["organization_proposals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsibility_resident_id"], ["residents.id"], ondelete="SET NULL"),
        sa.CheckConstraint("amount_minor >= 0", name="ck_organization_commitments_amount_nonnegative"),
        sa.CheckConstraint("status IN ('active', 'fulfilled', 'breached', 'cancelled')", name="ck_organization_commitments_status_valid"),
    )
    op.create_index("ix_organization_commitments_due", "organization_commitments", ["status", "due_at", "id"])
    op.create_table(
        "organization_relationships",
        sa.Column("from_organization_id", sa.Integer(), primary_key=True),
        sa.Column("to_organization_id", sa.Integer(), primary_key=True),
        sa.Column("relation_type", sa.String(24), nullable=False, server_default="neutral"),
        sa.Column("trust", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("influence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["from_organization_id"], ["campus_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_organization_id"], ["campus_organizations.id"], ondelete="CASCADE"),
        sa.CheckConstraint("from_organization_id <> to_organization_id", name="ck_organization_relationships_distinct"),
        sa.CheckConstraint("relation_type IN ('neutral', 'alliance', 'service', 'competition', 'conflict')", name="ck_organization_relationships_type_valid"),
        sa.CheckConstraint("trust BETWEEN 0 AND 100", name="ck_organization_relationships_trust_valid"),
        sa.CheckConstraint("influence BETWEEN -100 AND 100", name="ck_organization_relationships_influence_valid"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_organization_relationships_status_valid"),
    )
    op.create_table(
        "organization_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(200), nullable=False, unique=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer()),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposal_id"], ["organization_proposals.id"], ondelete="SET NULL"),
        sa.CheckConstraint("severity IN ('info', 'warning', 'critical')", name="ck_organization_events_severity_valid"),
    )
    op.create_index("ix_organization_events_org", "organization_events", ["organization_id", "id"])


def downgrade() -> None:
    op.drop_index("ix_organization_events_org", table_name="organization_events")
    op.drop_table("organization_events")
    op.drop_table("organization_relationships")
    op.drop_index("ix_organization_commitments_due", table_name="organization_commitments")
    op.drop_table("organization_commitments")
    op.drop_table("organization_votes")
    op.drop_index("ix_organization_proposals_due", table_name="organization_proposals")
    op.drop_table("organization_proposals")
    op.drop_table("organization_role_assignments")
    op.drop_index("ix_organization_roles_org_status", table_name="organization_roles")
    op.drop_table("organization_roles")
    op.drop_table("organization_runtime_profiles")
