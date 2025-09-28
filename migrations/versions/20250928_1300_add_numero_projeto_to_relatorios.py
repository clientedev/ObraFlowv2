"""add numero_projeto to relatorios

Revision ID: 20250928_1300
Revises: 20250928_0119
Create Date: 2025-09-28 13:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250928_1300'
down_revision = 'c18fc0f1e85a'
branch_labels = None
depends_on = None

def upgrade():
    """Add numero_projeto column to relatorios table for project-specific numbering"""
    # Add numero_projeto column to relatorios table
    op.add_column('relatorios', 
                  sa.Column('numero_projeto', sa.Integer(), nullable=True))
    
    # Add comment to make the purpose clear
    op.execute("COMMENT ON COLUMN relatorios.numero_projeto IS 'Sequential numbering within each project'")

def downgrade():
    """Remove numero_projeto column from relatorios table"""
    # Remove numero_projeto column from relatorios table
    op.drop_column('relatorios', 'numero_projeto')