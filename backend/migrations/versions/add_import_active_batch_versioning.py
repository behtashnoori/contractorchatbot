"""Add active batch versioning for imported datasets.

Revision ID: import_active_batch
Revises: norm_import_status
Create Date: 2026-06-06

"""

from alembic import op
import sqlalchemy as sa


revision = "import_active_batch"
down_revision = "norm_import_status"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "contractor",
        sa.Column("last_update_batch_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "contractor",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_foreign_key(
        "fk_contractor_last_update_batch_id_importbatch",
        "contractor",
        "importbatch",
        ["last_update_batch_id"],
        ["id"],
    )
    op.drop_index("ix_contractor_detail_code", table_name="contractor")
    op.create_index(
        "ix_contractor_detail_code",
        "contractor",
        ["detail_code"],
        unique=False,
    )
    op.create_index(
        "uq_contractor_active_detail_code",
        "contractor",
        ["detail_code"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.add_column(
        "invoicesummary",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(
        "ix_invoicesummary_is_active",
        "invoicesummary",
        ["is_active"],
        unique=False,
    )

    op.add_column(
        "invoicedetail",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(
        "ix_invoicedetail_is_active",
        "invoicedetail",
        ["is_active"],
        unique=False,
    )

    op.add_column("importbatch", sa.Column("published_at", sa.DateTime(), nullable=True))
    op.add_column(
        "importbatch",
        sa.Column("replaced_by_batch_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_importbatch_replaced_by_batch_id_importbatch",
        "importbatch",
        "importbatch",
        ["replaced_by_batch_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_importbatch_replaced_by_batch_id_importbatch",
        "importbatch",
        type_="foreignkey",
    )
    op.drop_column("importbatch", "replaced_by_batch_id")
    op.drop_column("importbatch", "published_at")

    op.drop_index("ix_invoicedetail_is_active", table_name="invoicedetail")
    op.drop_column("invoicedetail", "is_active")

    op.drop_index("ix_invoicesummary_is_active", table_name="invoicesummary")
    op.drop_column("invoicesummary", "is_active")

    op.drop_index("uq_contractor_active_detail_code", table_name="contractor")
    op.drop_index("ix_contractor_detail_code", table_name="contractor")
    op.create_index(
        "ix_contractor_detail_code",
        "contractor",
        ["detail_code"],
        unique=True,
    )
    op.drop_constraint(
        "fk_contractor_last_update_batch_id_importbatch",
        "contractor",
        type_="foreignkey",
    )
    op.drop_column("contractor", "is_active")
    op.drop_column("contractor", "last_update_batch_id")
