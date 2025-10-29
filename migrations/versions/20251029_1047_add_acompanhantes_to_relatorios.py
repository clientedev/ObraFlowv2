"""add acompanhantes to relatorios

Revision ID: 20251029_1047
Revises: 20251027_2330
Create Date: 2025-10-29 10:47:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from helpers import add_column_if_absent, drop_column_if_present


# revision identifiers, used by Alembic.
revision = '20251029_1047'
down_revision = '20251027_2330'
branch_labels = None
depends_on = None

def upgrade():
    # Add acompanhantes column to relatorios table if it doesn't exist
    add_column_if_absent(op, 'relatorios', sa.Column('acompanhantes', JSONB, nullable=True))

def downgrade():
    # Remove acompanhantes column from relatorios table
    drop_column_if_present(op, 'relatorios', 'acompanhantes')
