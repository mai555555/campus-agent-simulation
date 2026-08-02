"""Bridge a legacy database whose historical 0032 migration source was lost.

Revision ID: 20260731_0032
Revises: 20260730_0031
"""

from __future__ import annotations


revision = "20260731_0032"
down_revision = "20260730_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    raise RuntimeError(
        "Migration 20260731_0032 is a compatibility marker for an existing "
        "legacy database. Its original schema migration source is unavailable; "
        "do not apply this revision to a newly initialized database."
    )


def downgrade() -> None:
    raise RuntimeError("Compatibility marker revisions cannot be downgraded.")
