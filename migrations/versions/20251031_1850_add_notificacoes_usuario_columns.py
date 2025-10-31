
"""add notificacoes usuario columns

Revision ID: add_usuario_columns
Revises: 265f97ab88c1
Create Date: 2025-10-31 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_usuario_columns'
down_revision = '265f97ab88c1'
branch_labels = None
depends_on = None


def upgrade():
    # Verificar se as colunas já existem antes de adicionar
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('notificacoes')]
    
    if 'usuario_origem_id' not in columns:
        op.add_column('notificacoes', sa.Column('usuario_origem_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_notificacoes_usuario_origem',
            'notificacoes', 'user',
            ['usuario_origem_id'], ['id']
        )
    
    if 'usuario_destino_id' not in columns:
        op.add_column('notificacoes', sa.Column('usuario_destino_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_notificacoes_usuario_destino',
            'notificacoes', 'user',
            ['usuario_destino_id'], ['id']
        )


def downgrade():
    op.drop_constraint('fk_notificacoes_usuario_destino', 'notificacoes', type_='foreignkey')
    op.drop_column('notificacoes', 'usuario_destino_id')
    op.drop_constraint('fk_notificacoes_usuario_origem', 'notificacoes', type_='foreignkey')
    op.drop_column('notificacoes', 'usuario_origem_id')
