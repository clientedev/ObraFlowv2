"""add local field to fotos_relatorio and fotos_relatorios_express

Revision ID: 20251025_2115
Revises: 20251025_2010
Create Date: 2025-10-25 21:15:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251025_2115'
down_revision = '20251025_2010'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    # Add local column to fotos_relatorio table (if not exists)
    if not column_exists('fotos_relatorio', 'local'):
        op.add_column('fotos_relatorio', 
                      sa.Column('local', sa.String(length=300), nullable=True))
    
    # Add local column to fotos_relatorios_express table (if not exists)
    if not column_exists('fotos_relatorios_express', 'local'):
        op.add_column('fotos_relatorios_express', 
                      sa.Column('local', sa.String(length=300), nullable=True))

def downgrade():
    # Remove local column from both tables (if they exist)
    if column_exists('fotos_relatorio', 'local'):
        op.drop_column('fotos_relatorio', 'local')
    
    if column_exists('fotos_relatorios_express', 'local'):
        op.drop_column('fotos_relatorios_express', 'local')
