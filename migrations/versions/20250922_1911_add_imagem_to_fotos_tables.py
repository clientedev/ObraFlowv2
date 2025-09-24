"""add imagem to fotos tables

Revision ID: 20250922_1911
Revises: None
Create Date: 2025-09-22 19:11:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250922_1911'
down_revision = '20250124_1200'
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar coluna imagem à tabela fotos_relatorio
    op.add_column('fotos_relatorio', 
                  sa.Column('imagem', sa.LargeBinary(), nullable=True))
    
    # Adicionar coluna imagem à tabela fotos_relatorios_express
    op.add_column('fotos_relatorios_express', 
                  sa.Column('imagem', sa.LargeBinary(), nullable=True))

def downgrade():
    # Remover coluna imagem das tabelas
    op.drop_column('fotos_relatorio', 'imagem')
    op.drop_column('fotos_relatorios_express', 'imagem')