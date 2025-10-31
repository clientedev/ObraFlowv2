
"""ensure fcm_token column exists

Revision ID: 20251031_0010
Revises: 20251030_2100
Create Date: 2025-10-31 00:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present


# revision identifiers, used by Alembic.
revision = '20251031_0010'
down_revision = '20251030_2100'
branch_labels = None
depends_on = None

def upgrade():
    """Add fcm_token column to users table if it doesn't exist"""
    # Verificar se a coluna já existe antes de adicionar
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'fcm_token' not in columns:
        # Adicionar coluna fcm_token à tabela users
        add_column_if_absent(op, 'users', 
                             sa.Column('fcm_token', sa.Text(), nullable=True))
        print("✅ Coluna 'fcm_token' adicionada à tabela 'users'.")
    else:
        print("ℹ️ Coluna 'fcm_token' já existe na tabela 'users' - pulando criação")

def downgrade():
    """Remove fcm_token column from users table if it exists"""
    # Remover coluna fcm_token da tabela users
    drop_column_if_present(op, 'users', 'fcm_token')
    print("🗑️ Coluna 'fcm_token' removida da tabela 'users'.")
