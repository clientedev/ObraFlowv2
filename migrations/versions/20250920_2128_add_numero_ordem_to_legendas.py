
"""add numero_ordem to legendas

Revision ID: add_numero_ordem_legendas
Revises: 20250920_1920_add_updated_at_to_relatorios
Create Date: 2025-09-20 21:28:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_numero_ordem_legendas'
down_revision = '20250920_1920_add_updated_at_to_relatorios'
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar coluna numero_ordem à tabela legendas_predefinidas
    op.add_column('legendas_predefinidas', 
                  sa.Column('numero_ordem', sa.Integer(), nullable=True))
    
    # Atualizar registros existentes com valores de ordem baseados no ID
    op.execute("""
        UPDATE legendas_predefinidas 
        SET numero_ordem = id 
        WHERE numero_ordem IS NULL
    """)

def downgrade():
    # Remover coluna numero_ordem
    op.drop_column('legendas_predefinidas', 'numero_ordem')
