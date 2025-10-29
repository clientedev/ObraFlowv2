
"""add calendar features to visits

Revision ID: 20250124_1200
Revises: 20250123_1030
Create Date: 2025-01-24 12:00:00
"""

from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present, column_exists


# revision identifiers, used by Alembic.
revision = '20250124_1200'
down_revision = '20250123_1030'
branch_labels = None
depends_on = None

def upgrade():
    """Add calendar features to visits table"""
    bind = op.get_bind()
    
    # Adicionar coluna is_pessoal à tabela visitas
    add_column_if_absent(op, 'visitas', 
                  sa.Column('is_pessoal', sa.Boolean(), nullable=True, default=False))
    
    # Adicionar coluna criado_por à tabela visitas
    add_column_if_absent(op, 'visitas', 
                  sa.Column('criado_por', sa.Integer(), nullable=True))
    
    # Adicionar foreign key constraint para criado_por (verificar se não existe)
    from sqlalchemy import inspect
    inspector = inspect(bind)
    fks = [fk['name'] for fk in inspector.get_foreign_keys('visitas')]
    if 'fk_visitas_criado_por' not in fks:
        op.create_foreign_key('fk_visitas_criado_por', 'visitas', 'users', ['criado_por'], ['id'])
    
    # Atualizar registros existentes
    # Definir is_pessoal como False para todas as visitas existentes
    op.execute("UPDATE visitas SET is_pessoal = FALSE WHERE is_pessoal IS NULL")
    
    # Definir criado_por = responsavel_id para visitas existentes onde criado_por é NULL
    op.execute("UPDATE visitas SET criado_por = responsavel_id WHERE criado_por IS NULL")

def downgrade():
    """Remove calendar features from visits table"""
    
    # Remover foreign key constraint
    op.drop_constraint('fk_visitas_criado_por', 'visitas', type_='foreignkey')
    
    # Remover colunas
    drop_column_if_present(op, 'visitas', 'criado_por')
    drop_column_if_present(op, 'visitas', 'is_pessoal')
