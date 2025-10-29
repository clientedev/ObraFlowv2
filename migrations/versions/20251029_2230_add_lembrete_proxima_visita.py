"""add lembrete_proxima_visita to relatorios

Revision ID: 20251029_2230
Revises: 20251029_1159
Create Date: 2025-10-29 22:30:00
"""

from alembic import op
import sqlalchemy as sa
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present


# revision identifiers, used by Alembic.
revision = '20251029_2230'
down_revision = '20251029_1159'
branch_labels = None
depends_on = None

def upgrade():
    # Add lembrete_proxima_visita column to relatorios table if it doesn't exist
    add_column_if_absent(op, 'relatorios', sa.Column('lembrete_proxima_visita', sa.Text, nullable=True))

def downgrade():
    # Remove lembrete_proxima_visita column from relatorios table
    drop_column_if_present(op, 'relatorios', 'lembrete_proxima_visita')
