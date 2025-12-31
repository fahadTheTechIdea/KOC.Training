"""Add industry scenarios table

Revision ID: 001_add_industry_scenarios
Revises: 
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import JSON

# revision identifiers, used by Alembic.
revision = '001_add_industry_scenarios'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create industry_scenarios table
    op.create_table(
        'industry_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('industry', sa.String(length=50), nullable=False),
        sa.Column('scenario_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('icon_name', sa.String(length=255), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_industry_type', 'industry_scenarios', ['industry', 'scenario_type'])
    op.create_index('idx_industry_priority', 'industry_scenarios', ['industry', 'priority'])
    op.create_index(op.f('ix_industry_scenarios_industry'), 'industry_scenarios', ['industry'])


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_industry_scenarios_industry'), table_name='industry_scenarios')
    op.drop_index('idx_industry_priority', table_name='industry_scenarios')
    op.drop_index('idx_industry_type', table_name='industry_scenarios')
    
    # Drop table
    op.drop_table('industry_scenarios')
