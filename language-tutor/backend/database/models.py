from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.enums import Audience, Language, MessageRole, ProficiencyLevel, SubscriptionTier
from database.types import (
    AudienceEnum,
    LanguageEnum,
    MessageRoleEnum,
    ProficiencyLevelEnum,
    SubscriptionTierEnum,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[Language | None] = mapped_column(LanguageEnum, nullable=True)
    level: Mapped[ProficiencyLevel | None] = mapped_column(ProficiencyLevelEnum, nullable=True)
    audience: Mapped[Audience | None] = mapped_column(AudienceEnum, nullable=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SubscriptionTierEnum, default=SubscriptionTier.FREE, server_default="free"
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    cognitive_profile: Mapped["CognitiveProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language | None] = mapped_column(LanguageEnum, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="persona")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    persona_id: Mapped[int | None] = mapped_column(ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[MessageRole] = mapped_column(MessageRoleEnum, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="messages")
    persona: Mapped["Persona | None"] = relationship(back_populates="messages")


class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_style: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vocabulary_level: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grammar_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_speaking_cefr: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_session_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="cognitive_profile")


class SessionAssessment(Base):
    __tablename__ = "session_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    persona_id: Mapped[int | None] = mapped_column(ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    target_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user_message_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    speaking_cefr: Mapped[str | None] = mapped_column(String(10), nullable=True)
    mapped_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    grammar_focus: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()
    persona: Mapped["Persona | None"] = relationship()


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[Language] = mapped_column(LanguageEnum, index=True)
    level: Mapped[ProficiencyLevel] = mapped_column(ProficiencyLevelEnum, index=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    grade: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
