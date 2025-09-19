"""Add numero_relatorio column with per-project unique constraint

Revision ID: 001
Revises: 
Create Date: 2025-09-19 16:44:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add numero_relatorio column to relatorios table with per-project unique constraint.
    IDEMPOTENT: Safe to run multiple times, checks if changes already exist.
    """
    
    # Check if column already exists (handle schema drift)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('relatorios')]
    
    if 'numero_relatorio' not in columns:
        op.add_column('relatorios', 
                     sa.Column('numero_relatorio', sa.Integer(), nullable=True))
        print("✅ Added numero_relatorio column")
    else:
        print("⚠️ Column numero_relatorio already exists, skipping")
    
    # Check if constraint already exists
    constraints = [cons['name'] for cons in inspector.get_unique_constraints('relatorios')]
    
    if 'unique_report_number_per_project' not in constraints:
        op.create_unique_constraint(
            'unique_report_number_per_project',
            'relatorios', 
            ['projeto_id', 'numero_relatorio']
        )
        print("✅ Added unique constraint")
    else:
        print("⚠️ Constraint unique_report_number_per_project already exists, skipping")


def downgrade() -> None:
    """
    Remove the numero_relatorio column and associated constraint.
    
    WARNING: This will permanently delete the per-project numbering data!
    Only run this if you want to revert to global numbering system.
    """
    
    # Drop the unique constraint first
    op.drop_constraint('unique_report_number_per_project', 'relatorios', type_='unique')
    
    # Drop the numero_relatorio column
    op.drop_column('relatorios', 'numero_relatorio')