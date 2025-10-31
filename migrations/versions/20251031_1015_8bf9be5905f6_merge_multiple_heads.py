"""Merge multiple heads

Revision ID: 8bf9be5905f6
Revises: 20251029_2300, 20251031_0010
Create Date: 2025-10-31 10:15:44.792864

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bf9be5905f6'
down_revision = ('20251029_2300', '20251031_0010')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass