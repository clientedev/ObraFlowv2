"""add link_destino to notificacoes

Revision ID: 20251031_1420
Revises: 8bf9be5905f6
Create Date: 2025-10-31 14:20:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251031_1420'
down_revision = '8bf9be5905f6'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    """Add link_destino column to notificacoes table if it doesn't exist"""
    if not column_exists('notificacoes', 'link_destino'):
        with op.batch_alter_table('notificacoes', schema=None) as batch_op:
            batch_op.add_column(sa.Column('link_destino', sa.String(255), nullable=True))
        print("✅ Coluna 'link_destino' adicionada à tabela 'notificacoes'")
    else:
        print("ℹ️ Coluna 'link_destino' já existe na tabela 'notificacoes'")

def downgrade():
    """Remove link_destino column from notificacoes table"""
    if column_exists('notificacoes', 'link_destino'):
        with op.batch_alter_table('notificacoes', schema=None) as batch_op:
            batch_op.drop_column('link_destino')
        print("✅ Coluna 'link_destino' removida da tabela 'notificacoes'")
