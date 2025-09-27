"""add relatorio express participantes table

Revision ID: 20250927_2241
Revises: 20250922_1911
Create Date: 2025-09-27 22:41:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250927_2241'
down_revision = '20250922_1911'
branch_labels = None
depends_on = None

def upgrade():
    """Create relatorio_express_participantes table"""
    
    # Criar tabela relatorio_express_participantes
    op.create_table('relatorio_express_participantes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('relatorio_express_id', sa.Integer(), nullable=False),
        sa.Column('funcionario_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['relatorio_express_id'], ['relatorios_express.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['funcionario_id'], ['users.id'], ondelete='CASCADE')
    )

def downgrade():
    """Drop relatorio_express_participantes table"""
    
    # Remover tabela relatorio_express_participantes
    op.drop_table('relatorio_express_participantes')