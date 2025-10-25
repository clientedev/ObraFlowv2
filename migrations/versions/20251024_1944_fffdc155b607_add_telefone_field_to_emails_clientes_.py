"""add telefone field to emails_clientes and allow null email

Revision ID: fffdc155b607
Revises: f1a2b3c4d5e6
Create Date: 2025-10-24 19:44:50.440351

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'fffdc155b607'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('emails_clientes')]

    # Adicionar campo telefone à tabela emails_clientes (se não existir)
    if 'telefone' not in columns:
        op.add_column('emails_clientes', sa.Column('telefone', sa.String(20), nullable=True))
        print("✅ Coluna 'telefone' adicionada com sucesso.")
    else:
        print("⚠️ Coluna 'telefone' já existe — pulando criação.")
    
    # Modificar campo email para permitir NULL (se necessário)
    try:
        op.alter_column('emails_clientes', 'email',
                        existing_type=sa.String(255),
                        nullable=True)
        print("✅ Coluna 'email' modificada para permitir NULL.")
    except Exception as e:
        print(f"⚠️ Não foi possível alterar coluna 'email': {e}")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('emails_clientes')]

    # Remover campo telefone (se existir)
    if 'telefone' in columns:
        op.drop_column('emails_clientes', 'telefone')
        print("✅ Coluna 'telefone' removida com sucesso.")
    else:
        print("⚠️ Coluna 'telefone' não existe — pulando remoção.")
    
    # Reverter campo email para NOT NULL
    try:
        op.alter_column('emails_clientes', 'email',
                        existing_type=sa.String(255),
                        nullable=False)
        print("✅ Coluna 'email' revertida para NOT NULL.")
    except Exception as e:
        print(f"⚠️ Não foi possível reverter coluna 'email': {e}")