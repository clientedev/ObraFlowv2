"""fix numero unique constraint per project

Revision ID: 20250929_2100
Revises: 20250929_1845
Create Date: 2025-09-29 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '20250929_2100'
down_revision = '20250929_1845'
branch_labels = None
depends_on = None

def upgrade():
    """
    Fix the numero column to allow per-project numbering:
    1. Drop the global unique constraint on numero
    2. Add composite unique constraint on (projeto_id, numero)
    3. Fix existing numero values to use per-project numbering
    """
    conn = op.get_bind()
    
    # Step 1: Drop the existing unique constraint on numero column
    # First, get the constraint name
    result = conn.execute(text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'relatorios' 
        AND constraint_type = 'UNIQUE'
        AND constraint_name LIKE '%numero%'
    """))
    
    constraint_name = result.scalar()
    if constraint_name:
        op.drop_constraint(constraint_name, 'relatorios', type_='unique')
    
    # Step 2: Fix numero values to use per-project sequential numbering
    # Use ROW_NUMBER() to assign sequential numbers within each project
    conn.execute(text("""
        WITH ranked AS (
            SELECT id,
                   projeto_id,
                   ROW_NUMBER() OVER (PARTITION BY projeto_id ORDER BY created_at ASC) AS seq
            FROM relatorios
        )
        UPDATE relatorios r
        SET numero_projeto = ranked.seq,
            numero = 'REL-' || LPAD(ranked.seq::text, 4, '0')
        FROM ranked
        WHERE r.id = ranked.id
    """))
    
    # Step 3: Add composite unique constraint on (projeto_id, numero)
    op.create_unique_constraint(
        'uq_relatorios_projeto_numero', 
        'relatorios', 
        ['projeto_id', 'numero']
    )
    
    print("✅ Successfully fixed numero to use per-project numbering")

def downgrade():
    """Revert the changes"""
    conn = op.get_bind()
    
    # Drop the composite unique constraint
    op.drop_constraint('uq_relatorios_projeto_numero', 'relatorios', type_='unique')
    
    # Recreate the global unique constraint on numero
    op.create_unique_constraint('relatorios_numero_key', 'relatorios', ['numero'])
    
    print("⚠️ Reverted to global unique constraint on numero")
