from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    phone_number: Mapped[str | None] = mapped_column(String(32))
    google_refresh_token: Mapped[str | None] = mapped_column(Text)
    google_calendar_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    translate_target_lang: Mapped[str] = mapped_column(String(8), default="en")
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    digest_hour: Mapped[int] = mapped_column(default=8)
    digest_last_sent: Mapped[str | None] = mapped_column(String(10))
    pulse_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pulse_last_hour: Mapped[str | None] = mapped_column(String(13))
    ambient_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    night_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    night_hour: Mapped[int] = mapped_column(default=21)
    night_last_sent: Mapped[str | None] = mapped_column(String(10))
    traffic_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    traffic_origin: Mapped[str | None] = mapped_column(Text)
    traffic_destination: Mapped[str | None] = mapped_column(Text)
    traffic_threshold_min: Mapped[int] = mapped_column(default=15)
    traffic_check_start: Mapped[str | None] = mapped_column(String(5))
    traffic_check_end: Mapped[str | None] = mapped_column(String(5))
    traffic_last_alert: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[list[Task]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notes: Mapped[list[Note]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    journal_entries: Mapped[list[JournalEntry]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notify_message: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_call: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_phone: Mapped[bool] = mapped_column(Boolean, default=False)
    google_event_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="tasks")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="notes")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="chat_messages")


class JournalKind(str, enum.Enum):
    IDEA = "idea"
    EXPENSE = "expense"
    THOUGHT = "thought"
    DECISION = "decision"
    MOOD = "mood"
    INSIGHT = "insight"


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    content: Mapped[str] = mapped_column(Text)
    amount: Mapped[float | None] = mapped_column()
    currency: Mapped[str | None] = mapped_column(String(8))
    day_key: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="journal_entries")
