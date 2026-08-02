"""Bridge a legacy database already stamped at historical revision 0033.

Revision ID: 20260731_0033
Revises: 20260731_0032
"""

from __future__ import annotations


revision = "20260731_0033"
down_revision = "20260731_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise RuntimeError(
        "Migration 20260731_0033 is a compatibility marker for an existing "
        "legacy database. Its original schema migration source is unavailable; "
        "do not apply this revision to a newly initialized database."
    )


def downgrade() -> None:
    raise RuntimeError("Compatibility marker revisions cannot be downgraded.")
