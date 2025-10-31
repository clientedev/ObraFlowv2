"""add_relatorio_id_column_if_not_exists

Revision ID: a4d5b6d9c0ca
Revises: 
Create Date: 2025-10-31 16:47:05.044007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4d5b6d9c0ca'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona a coluna relatorio_id na tabela notificacoes se não existir
    # Usa SQL direto para verificar existência antes de adicionar
    conn = op.get_bind()
    
    # Verifica se a coluna já existe
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='notificacoes' AND column_name='relatorio_id'
    """))
    
    column_exists = result.fetchone() is not None
    
    if not column_exists:
        # Adiciona a coluna relatorio_id
        op.add_column('notificacoes', sa.Column('relatorio_id', sa.Integer(), nullable=True))
        
        # Adiciona a foreign key
        op.create_foreign_key(
            'fk_notificacoes_relatorio_id',
            'notificacoes', 'relatorios',
            ['relatorio_id'], ['id']
        )


def downgrade() -> None:
    # Remove a foreign key e a coluna se necessário
    conn = op.get_bind()
    
    # Verifica se a coluna existe antes de tentar remover
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='notificacoes' AND column_name='relatorio_id'
    """))
    
    column_exists = result.fetchone() is not None
    
    if column_exists:
        op.drop_constraint('fk_notificacoes_relatorio_id', 'notificacoes', type_='foreignkey')
        op.drop_column('notificacoes', 'relatorio_id')