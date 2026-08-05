"""Add grade to knowledge_chunks

Revision ID: 003
Revises: 002
Create Date: 2026-08-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_chunks", sa.Column("grade", sa.Integer(), nullable=True))
    op.create_index("ix_knowledge_chunks_grade", "knowledge_chunks", ["grade"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_grade", table_name="knowledge_chunks")
    op.drop_column("knowledge_chunks", "grade")
