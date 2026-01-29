"""add_segment_role_to_tasks

Revision ID: e9fe5c86f21b
Revises: b5d687703193
Create Date: 2026-01-24 04:13:28.456089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9fe5c86f21b'
down_revision: Union[str, None] = 'b5d687703193'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # segment_roleカラムを追加（'current', 'next', NULL）
    # BFSタスクのセグメント役割を管理（current/next制御用）
    op.add_column(
        'tasks',
        sa.Column('segment_role', sa.String(10), nullable=True)
    )
    # インデックスを追加（phaseとsegment_roleの組み合わせで検索）
    op.create_index(
        'idx_phase_segment_role',
        'tasks',
        ['phase', 'segment_role']
    )


def downgrade() -> None:
    op.drop_index('idx_phase_segment_role', table_name='tasks')
    op.drop_column('tasks', 'segment_role')
