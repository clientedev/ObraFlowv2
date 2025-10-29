"""add imagem to fotos tables

Revision ID: 20250922_1911
Revises: None
Create Date: 2025-09-22 19:11:00
"""

from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present


# revision identifiers, used by Alembic.
revision = '20250922_1911'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar coluna imagem à tabela fotos_relatorio se não existir
    add_column_if_absent(op, 'fotos_relatorio', 
                      sa.Column('imagem', sa.LargeBinary(), nullable=True))
    
    # Adicionar coluna imagem à tabela fotos_relatorios_express se não existir
    add_column_if_absent(op, 'fotos_relatorios_express', 
                      sa.Column('imagem', sa.LargeBinary(), nullable=True))

def downgrade():
    # Remover coluna imagem das tabelas
    drop_column_if_present(op, 'fotos_relatorio', 'imagem')
    drop_column_if_present(op, 'fotos_relatorios_express', 'imagem')