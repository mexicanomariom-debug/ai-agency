"""Add vocabulary_cards for FSRS spaced repetition

Revision ID: 007
Revises: 006
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vocabulary_cards (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            word VARCHAR(255) NOT NULL,
            translation VARCHAR(512) NOT NULL,
            example TEXT,
            target_language VARCHAR(32),
            fsrs_card_json TEXT NOT NULL,
            due_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            reps INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vocabulary_user_word_lang
        ON vocabulary_cards (user_id, word, target_language)
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vocabulary_cards_user_due ON vocabulary_cards (user_id, due_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_vocabulary_cards_user_due")
    op.execute("DROP INDEX IF EXISTS uq_vocabulary_user_word_lang")
    op.execute("DROP TABLE IF EXISTS vocabulary_cards")
