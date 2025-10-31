
"""add expires_at to notificacoes

Revision ID: 20251031_1430
Revises: 20251031_1420
Create Date: 2025-10-31 14:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251031_1430'
down_revision = '20251031_1420'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    """Add expires_at column to notificacoes table if it doesn't exist"""
    if not column_exists('notificacoes', 'expires_at'):
        op.add_column('notificacoes', 
                     sa.Column('expires_at', sa.DateTime(), nullable=True))
        print("✅ Coluna 'expires_at' adicionada à tabela 'notificacoes'")
    else:
        print("ℹ️ Coluna 'expires_at' já existe na tabela 'notificacoes'")

def downgrade():
    """Remove expires_at column from notificacoes table"""
    if column_exists('notificacoes', 'expires_at'):
        op.drop_column('notificacoes', 'expires_at')
        print("✅ Coluna 'expires_at' removida da tabela 'notificacoes'")
