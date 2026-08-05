"""Add session_assessments table

Revision ID: 005
Revises: 004
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Raw SQL avoids SQLAlchemy confusing column/type name "language" with PG enum.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS session_assessments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            persona_id INTEGER REFERENCES personas(id) ON DELETE SET NULL,
            target_language VARCHAR(32),
            user_message_count INTEGER NOT NULL DEFAULT 0,
            speaking_cefr VARCHAR(10),
            mapped_level VARCHAR(32),
            confidence VARCHAR(20),
            strengths TEXT,
            weaknesses TEXT,
            grammar_focus TEXT,
            recommendation TEXT,
            summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_session_assessments_user_id ON session_assessments (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_session_assessments_user_id")
    op.execute("DROP TABLE IF EXISTS session_assessments")
