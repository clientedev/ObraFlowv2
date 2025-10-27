"""add numeracao_inicial to projetos

Revision ID: 20251027_2330
Revises: 20251027_1930
Create Date: 2025-10-27 23:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251027_2330'
down_revision = '20251027_1930'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    # Add numeracao_inicial column to projetos table if it doesn't exist
    if not column_exists('projetos', 'numeracao_inicial'):
        with op.batch_alter_table('projetos', schema=None) as batch_op:
            batch_op.add_column(sa.Column('numeracao_inicial', sa.Integer(), nullable=False, server_default='1'))

def downgrade():
    # Remove numeracao_inicial column from projetos table
    with op.batch_alter_table('projetos', schema=None) as batch_op:
        batch_op.drop_column('numeracao_inicial')
