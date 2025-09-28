"""add_user_email_config_table

Revision ID: c18fc0f1e85a
Revises: 0611ef3ce130
Create Date: 2025-09-28 01:19:32.762489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c18fc0f1e85a'
down_revision = '0611ef3ce130'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_email_config table
    op.create_table(
        'user_email_config',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('smtp_server', sa.String(255), nullable=False),
        sa.Column('smtp_port', sa.Integer, nullable=False, default=587),
        sa.Column('email_address', sa.String(255), nullable=False),
        sa.Column('email_password', sa.Text, nullable=False),  # Will store encrypted/encoded password
        sa.Column('use_tls', sa.Boolean, nullable=False, default=True),
        sa.Column('use_ssl', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', name='unique_user_email_config')
    )
    
    # Create index for faster lookups
    op.create_index('idx_user_email_config_user_id', 'user_email_config', ['user_id'])


def downgrade() -> None:
    # Drop index first
    op.drop_index('idx_user_email_config_user_id')
    
    # Drop table
    op.drop_table('user_email_config')