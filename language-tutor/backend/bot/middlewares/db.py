from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import async_session_factory


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict[str, Any]):
        async with async_session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
