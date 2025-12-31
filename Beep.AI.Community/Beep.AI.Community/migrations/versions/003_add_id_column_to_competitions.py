"""Add id_column field to competitions

Revision ID: 003
Revises: 002
Create Date: 2025-12-20 14:34:16.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Add id_column field (nullable) - column name to exclude from features
    op.add_column('competitions', sa.Column('id_column', sa.String(length=100), nullable=True))


def downgrade():
    # Remove id_column field
    op.drop_column('competitions', 'id_column')
