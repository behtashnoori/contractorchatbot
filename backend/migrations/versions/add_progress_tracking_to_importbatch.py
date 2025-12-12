"""Add progress tracking to ImportBatch

Revision ID: add_progress_tracking
Revises: 040054c6f772
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_progress_tracking'
down_revision = '040054c6f772'
branch_labels = None
depends_on = None


def upgrade():
    # Add progress tracking columns to importbatch table
    op.add_column('importbatch', sa.Column('total_rows', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('importbatch', sa.Column('rows_processed', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('importbatch', sa.Column('progress_percentage', sa.Float(), nullable=True, server_default='0.0'))
    # Add import metrics columns
    op.add_column('importbatch', sa.Column('inserted_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('importbatch', sa.Column('updated_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('importbatch', sa.Column('errors_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Remove import metrics columns
    op.drop_column('importbatch', 'errors_count')
    op.drop_column('importbatch', 'updated_count')
    op.drop_column('importbatch', 'inserted_count')
    # Remove progress tracking columns
    op.drop_column('importbatch', 'progress_percentage')
    op.drop_column('importbatch', 'rows_processed')
    op.drop_column('importbatch', 'total_rows')

