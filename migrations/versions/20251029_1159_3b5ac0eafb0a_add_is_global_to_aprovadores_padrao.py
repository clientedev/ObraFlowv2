"""add_is_global_to_aprovadores_padrao

Revision ID: 20251029_1159
Revises: 20251029_1047
Create Date: 2025-10-29 11:59:45.139246

"""
from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present


# revision identifiers, used by Alembic.
revision = '20251029_1159'
down_revision = '20251029_1047'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campo is_global com valor padrão False se não existir
    add_column_if_absent(op, 'aprovadores_padrao', sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'))
    
    # Remover server_default após a adição
    try:
        op.alter_column('aprovadores_padrao', 'is_global', server_default=None)
    except Exception:
        pass  # Coluna pode já existir sem server_default
    
    # Atualizar registros existentes: se projeto_id é NULL, marcar como is_global=True
    op.execute("""
        UPDATE aprovadores_padrao
        SET is_global = TRUE
        WHERE projeto_id IS NULL AND ativo = TRUE AND is_global = FALSE
    """)
    
    # Garantir que apenas um aprovador global ativo exista
    # Se houver múltiplos, manter apenas o mais recente e desativar os outros
    op.execute("""
        WITH ranked_globals AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
            FROM aprovadores_padrao
            WHERE is_global = TRUE AND ativo = TRUE
        )
        UPDATE aprovadores_padrao
        SET ativo = FALSE
        WHERE id IN (
            SELECT id FROM ranked_globals WHERE rn > 1
        )
    """)


def downgrade():
    # Remover campo is_global
    drop_column_if_present(op, 'aprovadores_padrao', 'is_global')