"""add_is_global_to_aprovadores_padrao

Revision ID: 3b5ac0eafb0a
Revises: 20251029_1047
Create Date: 2025-10-29 11:59:45.139246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b5ac0eafb0a'
down_revision = '20251029_1047'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar campo is_global com valor padrão False
    op.add_column('aprovadores_padrao', sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'))
    
    # Atualizar registros existentes: se projeto_id é NULL, marcar como is_global=True
    op.execute("""
        UPDATE aprovadores_padrao
        SET is_global = TRUE
        WHERE projeto_id IS NULL AND ativo = TRUE
    """)
    
    # Remover server_default após a migração
    op.alter_column('aprovadores_padrao', 'is_global', server_default=None)
    
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


def downgrade() -> None:
    # Remover campo is_global
    op.drop_column('aprovadores_padrao', 'is_global')