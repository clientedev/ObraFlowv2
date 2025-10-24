"""add telefone field to emails_clientes and allow null email

Revision ID: fffdc155b607
Revises: f1a2b3c4d5e6
Create Date: 2025-10-24 19:44:50.440351

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fffdc155b607'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar campo telefone à tabela emails_clientes
    op.add_column('emails_clientes', sa.Column('telefone', sa.String(20), nullable=True))
    
    # Modificar campo email para permitir NULL
    op.alter_column('emails_clientes', 'email',
                    existing_type=sa.String(255),
                    nullable=True)


def downgrade() -> None:
    # Remover campo telefone
    op.drop_column('emails_clientes', 'telefone')
    
    # Reverter campo email para NOT NULL
    op.alter_column('emails_clientes', 'email',
                    existing_type=sa.String(255),
                    nullable=False)