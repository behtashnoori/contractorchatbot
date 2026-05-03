"""add auditlog table

Revision ID: add_auditlog
Revises: add_user_role
Create Date: 2026-05-03

"""

from alembic import op
import sqlalchemy as sa


revision = "add_auditlog"
down_revision = "add_user_role"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auditlog",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("auditlog", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_auditlog_action"), ["action"], unique=False)
        batch_op.create_index(batch_op.f("ix_auditlog_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("auditlog", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auditlog_user_id"))
        batch_op.drop_index(batch_op.f("ix_auditlog_action"))
    op.drop_table("auditlog")
