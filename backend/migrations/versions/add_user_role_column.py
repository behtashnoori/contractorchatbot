"""add user.role for RBAC

Revision ID: add_user_role
Revises: add_progress_tracking
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa


revision = "add_user_role"
down_revision = "add_progress_tracking"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "role",
            sa.String(length=32),
            nullable=False,
            server_default="contractor",
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            '''
            UPDATE "user" SET role = 'staff'
            WHERE lower(username) LIKE 'admin%%' OR lower(username) = 'expert'
            '''
        )
    )


def downgrade():
    op.drop_column("user", "role")
