"""add checklist obra completion tracking

Revision ID: 20260221_checklist_completion
Revises: 0d8a27655353
Create Date: 2026-02-21 20:30:00

Adds concluido, concluido_relatorio_id, concluido_em to checklist_obra
so each project-stage checklist item can track which report marked it done.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260221_checklist_completion'
down_revision = '0d8a27655353'
branch_labels = None
depends_on = None


def upgrade():
    # Add completion tracking columns to checklist_obra
    with op.batch_alter_table('checklist_obra', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'concluido',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE')
        ))
        batch_op.add_column(sa.Column(
            'concluido_relatorio_id',
            sa.Integer(),
            nullable=True
        ))
        batch_op.add_column(sa.Column(
            'concluido_em',
            sa.DateTime(),
            nullable=True
        ))
        batch_op.create_foreign_key(
            'fk_checklist_obra_relatorio',
            'relatorios',
            ['concluido_relatorio_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade():
    with op.batch_alter_table('checklist_obra', schema=None) as batch_op:
        batch_op.drop_constraint('fk_checklist_obra_relatorio', type_='foreignkey')
        batch_op.drop_column('concluido_em')
        batch_op.drop_column('concluido_relatorio_id')
        batch_op.drop_column('concluido')
