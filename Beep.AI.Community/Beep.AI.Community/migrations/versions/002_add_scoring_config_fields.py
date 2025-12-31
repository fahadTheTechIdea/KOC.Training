"""Add scoring configuration fields to competitions

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add target_column field (nullable) - legacy support
    op.add_column('competitions', sa.Column('target_column', sa.String(length=100), nullable=True))
    
    # Add task configuration fields
    op.add_column('competitions', sa.Column('task_type', sa.String(length=50), nullable=True))
    op.add_column('competitions', sa.Column('target_columns', sa.Text(), nullable=True))  # JSON array
    op.add_column('competitions', sa.Column('prediction_format', sa.String(length=50), nullable=True))
    op.add_column('competitions', sa.Column('evaluation_config', sa.Text(), nullable=True))  # JSON object


def downgrade():
    # Remove task configuration fields
    op.drop_column('competitions', 'evaluation_config')
    op.drop_column('competitions', 'prediction_format')
    op.drop_column('competitions', 'target_columns')
    op.drop_column('competitions', 'task_type')
    
    # Remove target_column field
    op.drop_column('competitions', 'target_column')
