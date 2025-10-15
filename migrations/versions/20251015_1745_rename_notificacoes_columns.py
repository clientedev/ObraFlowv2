"""rename_notificacoes_columns

Revision ID: f1a2b3c4d5e6
Revises: 20251003_0100_add_image_metadata_fields
Create Date: 2025-10-15 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '20251003_0100'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Renomeia as colunas da tabela notificacoes para corrigir o erro:
    - remetente_id -> usuario_origem_id
    - destinatario_id -> usuario_destino_id
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Verificar se a tabela existe
    if 'notificacoes' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('notificacoes')]
        
        # Renomear remetente_id para usuario_origem_id (se existir)
        if 'remetente_id' in columns and 'usuario_origem_id' not in columns:
            op.alter_column('notificacoes', 'remetente_id',
                          new_column_name='usuario_origem_id')
            print("✅ Coluna 'remetente_id' renomeada para 'usuario_origem_id'")
        
        # Renomear destinatario_id para usuario_destino_id (se existir)
        if 'destinatario_id' in columns and 'usuario_destino_id' not in columns:
            op.alter_column('notificacoes', 'destinatario_id',
                          new_column_name='usuario_destino_id')
            print("✅ Coluna 'destinatario_id' renomeada para 'usuario_destino_id'")
        
        # Adicionar campo email_sucesso se não existir
        if 'email_sucesso' not in columns:
            op.add_column('notificacoes',
                         sa.Column('email_sucesso', sa.Boolean(), nullable=True))
            print("✅ Coluna 'email_sucesso' adicionada")
        
        # Adicionar campo email_erro se não existir
        if 'email_erro' not in columns:
            op.add_column('notificacoes',
                         sa.Column('email_erro', sa.Text(), nullable=True))
            print("✅ Coluna 'email_erro' adicionada")
        
        # Adicionar campo status se não existir
        if 'status' not in columns:
            op.add_column('notificacoes',
                         sa.Column('status', sa.String(20), nullable=True))
            # Atualizar registros existentes
            op.execute("UPDATE notificacoes SET status = 'nao_lida' WHERE status IS NULL")
            print("✅ Coluna 'status' adicionada")
        
        # Adicionar campo lida_em se não existir (renomear data_leitura se existir)
        if 'data_leitura' in columns and 'lida_em' not in columns:
            op.alter_column('notificacoes', 'data_leitura',
                          new_column_name='lida_em')
            print("✅ Coluna 'data_leitura' renomeada para 'lida_em'")
        elif 'lida_em' not in columns and 'data_leitura' not in columns:
            op.add_column('notificacoes',
                         sa.Column('lida_em', sa.DateTime(), nullable=True))
            print("✅ Coluna 'lida_em' adicionada")


def downgrade() -> None:
    """
    Reverte as alterações (renomeia de volta para os nomes originais)
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'notificacoes' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('notificacoes')]
        
        # Reverter usuario_origem_id para remetente_id
        if 'usuario_origem_id' in columns:
            op.alter_column('notificacoes', 'usuario_origem_id',
                          new_column_name='remetente_id')
        
        # Reverter usuario_destino_id para destinatario_id
        if 'usuario_destino_id' in columns:
            op.alter_column('notificacoes', 'usuario_destino_id',
                          new_column_name='destinatario_id')
        
        # Remover email_sucesso se existir
        if 'email_sucesso' in columns:
            op.drop_column('notificacoes', 'email_sucesso')
        
        # Remover email_erro se existir
        if 'email_erro' in columns:
            op.drop_column('notificacoes', 'email_erro')
        
        # Remover status se existir
        if 'status' in columns:
            op.drop_column('notificacoes', 'status')
        
        # Reverter lida_em para data_leitura
        if 'lida_em' in columns:
            op.alter_column('notificacoes', 'lida_em',
                          new_column_name='data_leitura')
