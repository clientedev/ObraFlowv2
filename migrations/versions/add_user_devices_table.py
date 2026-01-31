"""add user_devices table for multi-device push notifications

Revision ID: add_user_devices
Revises: 
Create Date: 2026-01-31 17:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_devices'
down_revision = None  # Will be set by running alembic revision --autogenerate
branch_labels = None
depends_on = None


def upgrade():
    # Create user_devices table
    op.create_table('user_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.String(length=255), nullable=False),
        sa.Column('device_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('last_active', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id'),
        sa.UniqueConstraint('user_id', 'player_id', name='uq_user_player')
    )
    
    # Create indexes for performance
    op.create_index('idx_user_devices_user_id', 'user_devices', ['user_id'])
    op.create_index('idx_user_devices_player_id', 'user_devices', ['player_id'])
    
    # Migrate existing fcm_token data to user_devices
    # This will run as SQL to handle existing data
    op.execute("""
        INSERT INTO user_devices (user_id, player_id, device_info)
        SELECT id, fcm_token, 'Migrated from fcm_token column'
        FROM usuario
        WHERE fcm_token IS NOT NULL 
        AND fcm_token != ''
        ON CONFLICT (player_id) DO NOTHING
    """)


def downgrade():
    # Drop indexes
    op.drop_index('idx_user_devices_player_id', table_name='user_devices')
    op.drop_index('idx_user_devices_user_id', table_name='user_devices')
    
    # Drop table
    op.drop_table('user_devices')
