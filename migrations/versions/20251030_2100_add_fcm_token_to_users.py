
"""add fcm_token to users

Revision ID: 20251030_2100
Revises: 20251029_2230
Create Date: 2025-10-30 21:00:00
"""

from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present


# revision identifiers, used by Alembic.
revision = '20251030_2100'
down_revision = '20251029_2230'
branch_labels = None
depends_on = None

def upgrade():
    """Add fcm_token column to users table if it doesn't exist"""
    # Adicionar coluna fcm_token à tabela users
    add_column_if_absent(op, 'users', 
                         sa.Column('fcm_token', sa.String(255), nullable=True))
    print("✅ Migração concluída: coluna 'fcm_token' verificada/adicionada à tabela 'users'.")

def downgrade():
    """Remove fcm_token column from users table if it exists"""
    # Remover coluna fcm_token da tabela users
    drop_column_if_present(op, 'users', 'fcm_token')
    print("🗑️ Coluna 'fcm_token' removida da tabela 'users'.")
