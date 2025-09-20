
"""add updated_at to relatorios

Revision ID: add_updated_at_relatorios
Revises: 42776d8c4e78
Create Date: 2025-09-20 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_updated_at_relatorios'
down_revision = '42776d8c4e78'
branch_labels = None
depends_on = None

def upgrade():
    # Add updated_at column to relatorios table
    op.add_column('relatorios', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Set default value for existing records
    op.execute("UPDATE relatorios SET updated_at = created_at WHERE updated_at IS NULL")
    
    # Make column non-nullable after setting defaults
    op.alter_column('relatorios', 'updated_at', nullable=False)

def downgrade():
    # Remove updated_at column
    op.drop_column('relatorios', 'updated_at')
