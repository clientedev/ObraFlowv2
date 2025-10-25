"""remove is_principal hierarchy from emails_clientes

Revision ID: 20251025_2010
Revises: fffdc155b607
Create Date: 2025-10-25 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20251025_2010'
down_revision = 'fffdc155b607'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('emails_clientes')]

    # Remover campo is_principal (se existir)
    if 'is_principal' in columns:
        with op.batch_alter_table('emails_clientes', schema=None) as batch_op:
            batch_op.drop_column('is_principal')
        print("✅ Coluna 'is_principal' removida com sucesso - todos os contatos agora têm mesmo nível hierárquico.")
    else:
        print("⚠️ Coluna 'is_principal' não existe — pulando remoção.")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('emails_clientes')]

    # Restaurar campo is_principal (se não existir)
    if 'is_principal' not in columns:
        with op.batch_alter_table('emails_clientes', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_principal', sa.Boolean(), nullable=True, server_default='false'))
        print("✅ Coluna 'is_principal' restaurada.")
    else:
        print("⚠️ Coluna 'is_principal' já existe — pulando adição.")
