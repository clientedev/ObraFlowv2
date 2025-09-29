"""fix numero_projeto retroactively

Revision ID: 20250929_1845
Revises: 20250928_1300
Create Date: 2025-09-29 18:45:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '20250929_1845'
down_revision = '20250928_1300'
branch_labels = None
depends_on = None

def upgrade():
    """Populate numero_projeto retroactively for existing reports"""
    conn = op.get_bind()

    # Populate numero_projeto retroactively based on creation order within each project
    update_sql = """
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
    WHERE r.id = ranked.id;
    """
    conn.execute(text(update_sql))

def downgrade():
    """Revert numero_projeto population"""
    conn = op.get_bind()
    conn.execute(text("UPDATE relatorios SET numero_projeto = NULL;"))