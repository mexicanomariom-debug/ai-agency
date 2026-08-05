from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import MessageRole
from database.models import ChatMessage, Persona, User


class ChatHistoryService:
    async def add_message(
        self,
        session: AsyncSession,
        user: User,
        role: MessageRole,
        content: str,
        persona: Persona | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            user_id=user.id,
            persona_id=persona.id if persona else None,
            role=role,
            content=content,
        )
        session.add(message)
        await session.flush()
        return message

    async def get_recent(
        self,
        session: AsyncSession,
        user: User,
        limit: int = 20,
        persona: Persona | None = None,
    ) -> list[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.user_id == user.id)
        if persona:
            stmt = stmt.where(ChatMessage.persona_id == persona.id)
        stmt = stmt.order_by(ChatMessage.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    def to_openai_messages(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]


chat_history_service = ChatHistoryService()
