from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ChatMessage, User


class ChatHistoryService:
    async def add(self, session: AsyncSession, user: User, role: str, content: str) -> None:
        session.add(ChatMessage(user_id=user.id, role=role, content=content))

    async def get_recent(self, session: AsyncSession, user: User, limit: int = 10) -> list[dict[str, str]]:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return self.to_openai_messages(messages)

    @staticmethod
    def to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]


chat_history_service = ChatHistoryService()
