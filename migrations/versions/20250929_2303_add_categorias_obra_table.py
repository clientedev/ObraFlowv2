"""add categorias_obra table

Revision ID: 20250929_2303
Revises: 20250929_2100
Create Date: 2025-09-29 23:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '20250929_2303'
down_revision = '20250929_2100'
branch_labels = None
depends_on = None

def upgrade():
    """
    Create categorias_obra table for customizable categories per project - Item 16
    """
    # Check if table already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'categorias_obra' not in existing_tables:
        # Create the categorias_obra table
        op.create_table(
            'categorias_obra',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('projeto_id', sa.Integer(), nullable=False),
            sa.Column('nome_categoria', sa.String(length=100), nullable=False),
            sa.Column('ordem', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('projeto_id', 'nome_categoria', name='uq_categoria_por_projeto')
        )
        
        # Create index for faster queries
        op.create_index('ix_categorias_obra_projeto_id', 'categorias_obra', ['projeto_id'])
        
        print("✅ Tabela categorias_obra criada com sucesso - Item 16")
    else:
        print("ℹ️ Tabela categorias_obra já existe - pulando criação")

def downgrade():
    """Revert the changes"""
    op.drop_index('ix_categorias_obra_projeto_id', table_name='categorias_obra')
    op.drop_table('categorias_obra')
    print("⚠️ Tabela categorias_obra removida")
