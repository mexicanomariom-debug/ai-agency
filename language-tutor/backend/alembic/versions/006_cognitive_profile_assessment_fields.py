"""Add assessment fields to cognitive_profiles

Revision ID: 006
Revises: 005
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE cognitive_profiles ADD COLUMN IF NOT EXISTS last_speaking_cefr VARCHAR(10)")
    op.execute("ALTER TABLE cognitive_profiles ADD COLUMN IF NOT EXISTS last_session_summary TEXT")
    op.execute(
        "ALTER TABLE cognitive_profiles ADD COLUMN IF NOT EXISTS last_assessed_at TIMESTAMPTZ"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE cognitive_profiles DROP COLUMN IF EXISTS last_assessed_at")
    op.execute("ALTER TABLE cognitive_profiles DROP COLUMN IF EXISTS last_session_summary")
    op.execute("ALTER TABLE cognitive_profiles DROP COLUMN IF EXISTS last_speaking_cefr")
