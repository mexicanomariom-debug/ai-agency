"""Add assessment fields to cognitive_profiles

Revision ID: 006
Revises: 005
Create Date: 2026-08-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cognitive_profiles", sa.Column("last_speaking_cefr", sa.String(length=10), nullable=True))
    op.add_column("cognitive_profiles", sa.Column("last_session_summary", sa.Text(), nullable=True))
    op.add_column("cognitive_profiles", sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("cognitive_profiles", "last_assessed_at")
    op.drop_column("cognitive_profiles", "last_session_summary")
    op.drop_column("cognitive_profiles", "last_speaking_cefr")
