"""add acompanhantes to relatorios

Revision ID: 20251029_1047
Revises: 20251027_2330
Create Date: 2025-10-29 10:47:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251029_1047'
down_revision = '20251027_2330'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    # Add acompanhantes column to relatorios table if it doesn't exist
    if not column_exists('relatorios', 'acompanhantes'):
        with op.batch_alter_table('relatorios', schema=None) as batch_op:
            batch_op.add_column(sa.Column('acompanhantes', JSONB, nullable=True))

def downgrade():
    # Remove acompanhantes column from relatorios table
    with op.batch_alter_table('relatorios', schema=None) as batch_op:
        batch_op.drop_column('acompanhantes')
