"""add path_count to tasks

Revision ID: b5d687703193
Revises: 
Create Date: 2026-01-08 16:23:32.339632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5d687703193'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # path_countカラムを追加（到達パス数、多倍長整数文字列）
    op.add_column('tasks', sa.Column('path_count', sa.String(80), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('tasks', 'path_count')
