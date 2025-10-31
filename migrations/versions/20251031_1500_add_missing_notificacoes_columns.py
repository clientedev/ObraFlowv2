
"""add missing notification columns

Revision ID: 20251031_1500
Revises: 20251031_1430
Create Date: 2025-10-31 15:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251031_1500'
down_revision = '20251031_1430'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    """Add all missing columns to notificacoes table"""
    
    # Adicionar link_destino (se não existir)
    if not column_exists('notificacoes', 'link_destino'):
        op.add_column('notificacoes', 
                     sa.Column('link_destino', sa.String(255), nullable=True))
        print("✅ Coluna 'link_destino' adicionada")
    else:
        print("ℹ️ Coluna 'link_destino' já existe")
    
    # Adicionar email_enviado (se não existir)
    if not column_exists('notificacoes', 'email_enviado'):
        op.add_column('notificacoes', 
                     sa.Column('email_enviado', sa.Boolean(), nullable=False, server_default='false'))
        print("✅ Coluna 'email_enviado' adicionada")
    else:
        print("ℹ️ Coluna 'email_enviado' já existe")
    
    # Adicionar email_sucesso (se não existir)
    if not column_exists('notificacoes', 'email_sucesso'):
        op.add_column('notificacoes', 
                     sa.Column('email_sucesso', sa.Boolean(), nullable=True))
        print("✅ Coluna 'email_sucesso' adicionada")
    else:
        print("ℹ️ Coluna 'email_sucesso' já existe")
    
    # Adicionar email_erro (se não existir)
    if not column_exists('notificacoes', 'email_erro'):
        op.add_column('notificacoes', 
                     sa.Column('email_erro', sa.Text(), nullable=True))
        print("✅ Coluna 'email_erro' adicionada")
    else:
        print("ℹ️ Coluna 'email_erro' já existe")
    
    # Adicionar push_enviado (se não existir)
    if not column_exists('notificacoes', 'push_enviado'):
        op.add_column('notificacoes', 
                     sa.Column('push_enviado', sa.Boolean(), nullable=False, server_default='false'))
        print("✅ Coluna 'push_enviado' adicionada")
    else:
        print("ℹ️ Coluna 'push_enviado' já existe")
    
    # Adicionar push_sucesso (se não existir)
    if not column_exists('notificacoes', 'push_sucesso'):
        op.add_column('notificacoes', 
                     sa.Column('push_sucesso', sa.Boolean(), nullable=True))
        print("✅ Coluna 'push_sucesso' adicionada")
    else:
        print("ℹ️ Coluna 'push_sucesso' já existe")
    
    # Adicionar push_erro (se não existir)
    if not column_exists('notificacoes', 'push_erro'):
        op.add_column('notificacoes', 
                     sa.Column('push_erro', sa.Text(), nullable=True))
        print("✅ Coluna 'push_erro' adicionada")
    else:
        print("ℹ️ Coluna 'push_erro' já existe")
    
    # Adicionar expires_at (se não existir)
    if not column_exists('notificacoes', 'expires_at'):
        op.add_column('notificacoes', 
                     sa.Column('expires_at', sa.DateTime(), nullable=True))
        print("✅ Coluna 'expires_at' adicionada")
    else:
        print("ℹ️ Coluna 'expires_at' já existe")
    
    # Adicionar lida_em (se não existir)
    if not column_exists('notificacoes', 'lida_em'):
        op.add_column('notificacoes', 
                     sa.Column('lida_em', sa.DateTime(), nullable=True))
        print("✅ Coluna 'lida_em' adicionada")
    else:
        print("ℹ️ Coluna 'lida_em' já existe")

def downgrade():
    """Remove added columns from notificacoes table"""
    
    # Remover colunas adicionadas (se existirem)
    if column_exists('notificacoes', 'push_erro'):
        op.drop_column('notificacoes', 'push_erro')
        print("✅ Coluna 'push_erro' removida")
    
    if column_exists('notificacoes', 'push_sucesso'):
        op.drop_column('notificacoes', 'push_sucesso')
        print("✅ Coluna 'push_sucesso' removida")
    
    if column_exists('notificacoes', 'push_enviado'):
        op.drop_column('notificacoes', 'push_enviado')
        print("✅ Coluna 'push_enviado' removida")
    
    if column_exists('notificacoes', 'email_erro'):
        op.drop_column('notificacoes', 'email_erro')
        print("✅ Coluna 'email_erro' removida")
    
    if column_exists('notificacoes', 'email_sucesso'):
        op.drop_column('notificacoes', 'email_sucesso')
        print("✅ Coluna 'email_sucesso' removida")
    
    if column_exists('notificacoes', 'email_enviado'):
        op.drop_column('notificacoes', 'email_enviado')
        print("✅ Coluna 'email_enviado' removida")
    
    if column_exists('notificacoes', 'link_destino'):
        op.drop_column('notificacoes', 'link_destino')
        print("✅ Coluna 'link_destino' removida")
    
    if column_exists('notificacoes', 'lida_em'):
        op.drop_column('notificacoes', 'lida_em')
        print("✅ Coluna 'lida_em' removida")
    
    if column_exists('notificacoes', 'expires_at'):
        op.drop_column('notificacoes', 'expires_at')
        print("✅ Coluna 'expires_at' removida")
