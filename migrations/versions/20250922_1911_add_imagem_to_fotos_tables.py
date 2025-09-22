"""add imagem campo to fotos_relatorio and fotos_relatorios_express

Revision ID: add_imagem_fotos_tables
Revises: add_numero_ordem_legendas
Create Date: 2025-09-22 19:11:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_imagem_fotos_tables'
down_revision = 'add_numero_ordem_legendas'
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