"""add_checklist_obra_and_projeto_checklist_config_tables

Revision ID: 20251029_2300
Revises: 20251029_2230
Create Date: 2025-10-29 23:00:00

"""
from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import table_exists


# revision identifiers, used by Alembic.
revision = '20251029_2300'
down_revision = '20251029_2230'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Create checklist_obra table if it doesn't exist
    if not table_exists(conn, 'checklist_obra'):
        op.create_table('checklist_obra',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('projeto_id', sa.Integer(), nullable=False),
            sa.Column('texto', sa.String(length=500), nullable=False),
            sa.Column('ordem', sa.Integer(), nullable=True),
            sa.Column('ativo', sa.Boolean(), nullable=True),
            sa.Column('criado_por', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['criado_por'], ['users.id'], ),
            sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('projeto_id', 'ordem', name='unique_ordem_por_projeto')
        )
    
    # Create projeto_checklist_config table if it doesn't exist
    if not table_exists(conn, 'projeto_checklist_config'):
        op.create_table('projeto_checklist_config',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('projeto_id', sa.Integer(), nullable=False),
            sa.Column('tipo_checklist', sa.String(length=20), nullable=False),
            sa.Column('criado_por', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['criado_por'], ['users.id'], ),
            sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('projeto_id')
        )


def downgrade():
    # Drop tables if they exist
    op.drop_table('projeto_checklist_config')
    op.drop_table('checklist_obra')
