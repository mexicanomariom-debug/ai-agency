"""Add session_assessments table

Revision ID: 005
Revises: 004
Create Date: 2026-08-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LANGUAGE_VALUES = (
    "english",
    "spanish",
    "french",
    "german",
    "italian",
    "portuguese",
    "russian",
    "japanese",
    "korean",
    "chinese",
)

LEVEL_VALUES = (
    "beginner",
    "elementary",
    "intermediate",
    "upper_intermediate",
    "advanced",
    "native",
)


def upgrade() -> None:
    op.create_table(
        "session_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=True),
        sa.Column(
            "language",
            sa.Enum(*LANGUAGE_VALUES, name="language", create_type=False),
            nullable=True,
        ),
        sa.Column("user_message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("speaking_cefr", sa.String(length=10), nullable=True),
        sa.Column(
            "mapped_level",
            sa.Enum(*LEVEL_VALUES, name="proficiencylevel", create_type=False),
            nullable=True,
        ),
        sa.Column("confidence", sa.String(length=20), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("weaknesses", sa.Text(), nullable=True),
        sa.Column("grammar_focus", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["persona_id"], ["personas.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_assessments_user_id", "session_assessments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_session_assessments_user_id", table_name="session_assessments")
    op.drop_table("session_assessments")
