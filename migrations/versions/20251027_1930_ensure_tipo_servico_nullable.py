"""ensure tipo_servico is nullable in fotos tables

Revision ID: 20251027_1930
Revises: 20251025_2115
Create Date: 2025-10-27 19:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251027_1930'
down_revision = '20251025_2115'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    # Ensure tipo_servico column allows NULL in fotos_relatorio table
    if column_exists('fotos_relatorio', 'tipo_servico'):
        with op.batch_alter_table('fotos_relatorio', schema=None) as batch_op:
            batch_op.alter_column('tipo_servico',
                                  existing_type=sa.String(length=100),
                                  nullable=True)
    
    # Ensure tipo_servico column allows NULL in fotos_relatorios_express table
    if column_exists('fotos_relatorios_express', 'tipo_servico'):
        with op.batch_alter_table('fotos_relatorios_express', schema=None) as batch_op:
            batch_op.alter_column('tipo_servico',
                                  existing_type=sa.String(length=100),
                                  nullable=True)

def downgrade():
    # Note: We don't enforce NOT NULL on downgrade to avoid data loss
    # If needed, this can be manually adjusted
    pass
