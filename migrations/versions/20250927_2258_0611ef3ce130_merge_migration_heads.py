"""merge migration heads

Revision ID: 0611ef3ce130
Revises: 20250124_1200, 20250927_2241
Create Date: 2025-09-27 22:58:01.353872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0611ef3ce130'
down_revision = ('20250124_1200', '20250927_2241')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass