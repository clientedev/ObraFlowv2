
"""add cor_agenda to users

Revision ID: 20250123_1030
Revises: 20250922_1911
Create Date: 2025-01-23 10:30:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250123_1030'
down_revision = '20250922_1911'
branch_labels = None
depends_on = None

def upgrade():
    """Add cor_agenda column to users table"""
    # Adicionar coluna cor_agenda à tabela users
    op.add_column('users', 
                  sa.Column('cor_agenda', sa.String(7), nullable=True, default='#0EA5E9'))
    
    # Atualizar registros existentes com a cor padrão
    op.execute("UPDATE users SET cor_agenda = '#0EA5E9' WHERE cor_agenda IS NULL")

def downgrade():
    """Remove cor_agenda column from users table"""
    # Remover coluna cor_agenda da tabela users
    op.drop_column('users', 'cor_agenda')
