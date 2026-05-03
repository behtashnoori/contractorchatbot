"""Normalize importbatch.status to pending/processing/done/failed

Revision ID: norm_import_status
Revises: add_auditlog
Create Date: 2026-05-03

"""

from alembic import op


revision = "norm_import_status"
down_revision = "add_auditlog"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE importbatch SET status = 'pending' WHERE status = 'queued'"
    )
    op.execute(
        "UPDATE importbatch SET status = 'done' WHERE status IN ('completed', 'completed_with_errors')"
    )


def downgrade():
    op.execute("UPDATE importbatch SET status = 'completed' WHERE status = 'done'")
    op.execute(
        "UPDATE importbatch SET status = 'queued' "
        "WHERE status = 'pending' AND source IN ('contractors-1', 'contractors-2')"
    )
