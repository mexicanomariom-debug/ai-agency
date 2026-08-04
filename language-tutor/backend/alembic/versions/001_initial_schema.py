"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column(
            "language",
            sa.Enum(
                "english", "spanish", "french", "german", "italian",
                "portuguese", "russian", "japanese", "korean", "chinese",
                name="language",
            ),
            nullable=True,
        ),
        sa.Column(
            "level",
            sa.Enum(
                "beginner", "elementary", "intermediate", "upper_intermediate",
                "advanced", "native",
                name="proficiencylevel",
            ),
            nullable=True,
        ),
        sa.Column("subscription_tier", sa.Enum("free", "basic", "premium", name="subscriptiontier"), server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "personas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column(
            "language",
            sa.Enum(
                "english", "spanish", "french", "german", "italian",
                "portuguese", "russian", "japanese", "korean", "chinese",
                name="language",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("is_default", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personas_slug", "personas", ["slug"], unique=True)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.Enum("user", "assistant", "system", name="messagerole"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["persona_id"], ["personas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_user_id", "chat_messages", ["user_id"])

    op.create_table(
        "cognitive_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("weaknesses", sa.Text(), nullable=True),
        sa.Column("learning_style", sa.String(255), nullable=True),
        sa.Column("vocabulary_level", sa.String(255), nullable=True),
        sa.Column("grammar_notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "language",
            sa.Enum(
                "english", "spanish", "french", "german", "italian",
                "portuguese", "russian", "japanese", "korean", "chinese",
                name="language",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "level",
            sa.Enum(
                "beginner", "elementary", "intermediate", "upper_intermediate",
                "advanced", "native",
                name="proficiencylevel",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_chunks_language", "knowledge_chunks", ["language"])
    op.create_index("ix_knowledge_chunks_level", "knowledge_chunks", ["level"])
    op.create_index("ix_knowledge_chunks_topic", "knowledge_chunks", ["topic"])


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("cognitive_profiles")
    op.drop_table("chat_messages")
    op.drop_table("personas")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS subscriptiontier")
    op.execute("DROP TYPE IF EXISTS proficiencylevel")
    op.execute("DROP TYPE IF EXISTS language")
