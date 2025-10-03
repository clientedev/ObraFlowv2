"""add image metadata fields (hash, content_type, size) to fotos_relatorio

Revision ID: 20251003_0100
Revises: 20250929_2303
Create Date: 2025-10-03 01:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251003_0100'
down_revision = '20250929_2303'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    # Add image metadata columns to fotos_relatorio table (if not exists)
    if not column_exists('fotos_relatorio', 'imagem_hash'):
        op.add_column('fotos_relatorio', 
                      sa.Column('imagem_hash', sa.String(length=64), nullable=True))
    
    if not column_exists('fotos_relatorio', 'content_type'):
        op.add_column('fotos_relatorio', 
                      sa.Column('content_type', sa.String(length=100), nullable=True))
    
    if not column_exists('fotos_relatorio', 'imagem_size'):
        op.add_column('fotos_relatorio', 
                      sa.Column('imagem_size', sa.Integer(), nullable=True))
    
    # Add image metadata columns to fotos_relatorios_express table (if not exists)
    if not column_exists('fotos_relatorios_express', 'imagem_hash'):
        op.add_column('fotos_relatorios_express', 
                      sa.Column('imagem_hash', sa.String(length=64), nullable=True))
    
    if not column_exists('fotos_relatorios_express', 'content_type'):
        op.add_column('fotos_relatorios_express', 
                      sa.Column('content_type', sa.String(length=100), nullable=True))
    
    if not column_exists('fotos_relatorios_express', 'imagem_size'):
        op.add_column('fotos_relatorios_express', 
                      sa.Column('imagem_size', sa.Integer(), nullable=True))

def downgrade():
    # Remove metadata columns from both tables (if they exist)
    if column_exists('fotos_relatorio', 'imagem_size'):
        op.drop_column('fotos_relatorio', 'imagem_size')
    
    if column_exists('fotos_relatorio', 'content_type'):
        op.drop_column('fotos_relatorio', 'content_type')
    
    if column_exists('fotos_relatorio', 'imagem_hash'):
        op.drop_column('fotos_relatorio', 'imagem_hash')
    
    if column_exists('fotos_relatorios_express', 'imagem_size'):
        op.drop_column('fotos_relatorios_express', 'imagem_size')
    
    if column_exists('fotos_relatorios_express', 'content_type'):
        op.drop_column('fotos_relatorios_express', 'content_type')
    
    if column_exists('fotos_relatorios_express', 'imagem_hash'):
        op.drop_column('fotos_relatorios_express', 'imagem_hash')
