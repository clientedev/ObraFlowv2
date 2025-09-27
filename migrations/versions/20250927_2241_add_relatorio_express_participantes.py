"""add relatorio express participantes table

Revision ID: 20250927_2241
Revises: 20250922_1911
Create Date: 2025-09-27 22:41:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20250927_2241'
down_revision = '20250922_1911'
branch_labels = None
depends_on = None

def upgrade():
    """Create relatorio_express_participantes table"""
    
    # Check if table already exists before creating
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'relatorio_express_participantes' not in inspector.get_table_names():
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
    
    # Check if table exists before dropping
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'relatorio_express_participantes' in inspector.get_table_names():
        # Remover tabela relatorio_express_participantes
        op.drop_table('relatorio_express_participantes')