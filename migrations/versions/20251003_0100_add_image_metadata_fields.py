"""add image metadata fields (hash, content_type, size) to fotos_relatorio

Revision ID: 20251003_0100
Revises: 20250929_2303
Create Date: 2025-10-03 01:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251003_0100'
down_revision = '20250929_2303'
branch_labels = None
depends_on = None

def upgrade():
    # Add image metadata columns to fotos_relatorio table
    op.add_column('fotos_relatorio', 
                  sa.Column('imagem_hash', sa.String(length=64), nullable=True))
    op.add_column('fotos_relatorio', 
                  sa.Column('content_type', sa.String(length=100), nullable=True))
    op.add_column('fotos_relatorio', 
                  sa.Column('imagem_size', sa.Integer(), nullable=True))
    
    # Add image metadata columns to fotos_relatorios_express table (for consistency)
    op.add_column('fotos_relatorios_express', 
                  sa.Column('imagem_hash', sa.String(length=64), nullable=True))
    op.add_column('fotos_relatorios_express', 
                  sa.Column('content_type', sa.String(length=100), nullable=True))
    op.add_column('fotos_relatorios_express', 
                  sa.Column('imagem_size', sa.Integer(), nullable=True))

def downgrade():
    # Remove metadata columns from both tables
    op.drop_column('fotos_relatorio', 'imagem_size')
    op.drop_column('fotos_relatorio', 'content_type')
    op.drop_column('fotos_relatorio', 'imagem_hash')
    
    op.drop_column('fotos_relatorios_express', 'imagem_size')
    op.drop_column('fotos_relatorios_express', 'content_type')
    op.drop_column('fotos_relatorios_express', 'imagem_hash')
