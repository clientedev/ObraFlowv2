
"""add notification tracking columns

Revision ID: 8a3f9b2c5d1e
Revises: 265f97ab88c1
Create Date: 2025-10-31 19:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '8a3f9b2c5d1e'
down_revision = '265f97ab88c1'
branch_labels = None
depends_on = None


def column_exists(bind, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    bind = op.get_bind()
    
    # Add email tracking columns if they don't exist
    if not column_exists(bind, 'notificacoes', 'email_enviado'):
        op.add_column('notificacoes', sa.Column('email_enviado', sa.Boolean(), nullable=True, server_default='false'))
    
    if not column_exists(bind, 'notificacoes', 'email_sucesso'):
        op.add_column('notificacoes', sa.Column('email_sucesso', sa.Boolean(), nullable=True))
    
    if not column_exists(bind, 'notificacoes', 'email_erro'):
        op.add_column('notificacoes', sa.Column('email_erro', sa.Text(), nullable=True))
    
    # Add push notification tracking columns if they don't exist
    if not column_exists(bind, 'notificacoes', 'push_enviado'):
        op.add_column('notificacoes', sa.Column('push_enviado', sa.Boolean(), nullable=True, server_default='false'))
    
    if not column_exists(bind, 'notificacoes', 'push_sucesso'):
        op.add_column('notificacoes', sa.Column('push_sucesso', sa.Boolean(), nullable=True))
    
    if not column_exists(bind, 'notificacoes', 'push_erro'):
        op.add_column('notificacoes', sa.Column('push_erro', sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    
    # Remove columns if they exist
    if column_exists(bind, 'notificacoes', 'push_erro'):
        op.drop_column('notificacoes', 'push_erro')
    
    if column_exists(bind, 'notificacoes', 'push_sucesso'):
        op.drop_column('notificacoes', 'push_sucesso')
    
    if column_exists(bind, 'notificacoes', 'push_enviado'):
        op.drop_column('notificacoes', 'push_enviado')
    
    if column_exists(bind, 'notificacoes', 'email_erro'):
        op.drop_column('notificacoes', 'email_erro')
    
    if column_exists(bind, 'notificacoes', 'email_sucesso'):
        op.drop_column('notificacoes', 'email_sucesso')
    
    if column_exists(bind, 'notificacoes', 'email_enviado'):
        op.drop_column('notificacoes', 'email_enviado')
