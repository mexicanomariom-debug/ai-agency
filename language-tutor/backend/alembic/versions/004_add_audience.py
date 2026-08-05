"""Add audience to users

Revision ID: 004
Revises: 003
Create Date: 2026-08-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE audience AS ENUM ('child', 'teen', 'adult')")
    op.add_column(
        "users",
        sa.Column(
            "audience",
            sa.Enum("child", "teen", "adult", name="audience", create_type=False),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "audience")
    op.execute("DROP TYPE IF EXISTS audience")
