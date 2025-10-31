"""migrate notificacoes to new structure

Revision ID: 20251031_1500
Revises: 20251031_1420
Create Date: 2025-10-31 15:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251031_1500'
down_revision = '20251031_1420'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False

def table_exists(table_name):
    """Check if a table exists"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()

def upgrade():
    """Migrate notificacoes table to new structure"""
    
    if not table_exists('notificacoes'):
        # Criar tabela do zero se não existir
        op.create_table(
            'notificacoes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('tipo', sa.String(50), nullable=False),
            sa.Column('titulo', sa.String(200), nullable=False),
            sa.Column('mensagem', sa.Text(), nullable=False),
            sa.Column('link_destino', sa.String(500), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='nova'),
            sa.Column('lida_em', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        print("✅ Tabela 'notificacoes' criada com nova estrutura")
    else:
        # Migrar estrutura existente
        print("🔄 Migrando tabela 'notificacoes' para nova estrutura...")
        
        # Adicionar user_id se não existir
        if not column_exists('notificacoes', 'user_id'):
            with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
            print("✅ Coluna 'user_id' adicionada")
            
            # Copiar dados de usuario_destino_id para user_id se usuario_destino_id existir
            if column_exists('notificacoes', 'usuario_destino_id'):
                op.execute("UPDATE notificacoes SET user_id = usuario_destino_id WHERE usuario_destino_id IS NOT NULL")
                print("✅ Dados copiados de 'usuario_destino_id' para 'user_id'")
        
        # Garantir que tipo existe
        if not column_exists('notificacoes', 'tipo'):
            with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                batch_op.add_column(sa.Column('tipo', sa.String(50), nullable=True))
            op.execute("UPDATE notificacoes SET tipo = 'geral' WHERE tipo IS NULL")
            print("✅ Coluna 'tipo' adicionada")
        
        # Garantir que titulo existe
        if not column_exists('notificacoes', 'titulo'):
            with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                batch_op.add_column(sa.Column('titulo', sa.String(200), nullable=True))
            op.execute("UPDATE notificacoes SET titulo = 'Notificação' WHERE titulo IS NULL")
            print("✅ Coluna 'titulo' adicionada")
        
        # Garantir que mensagem existe
        if not column_exists('notificacoes', 'mensagem'):
            with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                batch_op.add_column(sa.Column('mensagem', sa.Text(), nullable=True))
            op.execute("UPDATE notificacoes SET mensagem = titulo WHERE mensagem IS NULL")
            print("✅ Coluna 'mensagem' adicionada")
        
        # link_destino já foi adicionado pela migration anterior
        
        # Atualizar status de 'nao_lida' para 'nova'
        if column_exists('notificacoes', 'status'):
            op.execute("UPDATE notificacoes SET status = 'nova' WHERE status = 'nao_lida' OR status IS NULL")
            print("✅ Status atualizado de 'nao_lida' para 'nova'")
        
        # Garantir que lida_em existe
        if not column_exists('notificacoes', 'lida_em'):
            with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                batch_op.add_column(sa.Column('lida_em', sa.DateTime(), nullable=True))
            print("✅ Coluna 'lida_em' adicionada")
        
        # Garantir que created_at existe
        if not column_exists('notificacoes', 'created_at'):
            with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
            print("✅ Coluna 'created_at' adicionada")
        
        # Remover colunas antigas que não são mais usadas
        colunas_para_remover = [
            'usuario_origem_id',
            'usuario_destino_id', 
            'relatorio_id',
            'email_enviado',
            'email_sucesso',
            'email_erro',
            'push_enviado',
            'push_sucesso',
            'expires_at'
        ]
        
        for coluna in colunas_para_remover:
            if column_exists('notificacoes', coluna):
                with op.batch_alter_table('notificacoes', schema=None) as batch_op:
                    batch_op.drop_column(coluna)
                print(f"✅ Coluna '{coluna}' removida")

def downgrade():
    """Revert migration - not recommended as data may be lost"""
    print("⚠️ Downgrade não implementado - pode resultar em perda de dados")
    pass
