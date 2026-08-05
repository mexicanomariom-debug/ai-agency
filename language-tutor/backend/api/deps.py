from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.telegram import get_demo_user, validate_telegram_init_data
from config import settings
from database.models import User
from database.session import get_session
from services.user_service import user_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_current_user(
    session: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    x_demo_mode: str | None = Header(None, alias="X-Demo-Mode"),
) -> User:
    if settings.demo_mode and x_demo_mode == "true":
        demo = get_demo_user()
        return await user_service.get_or_create(
            session,
            telegram_id=demo["id"],
            username=demo["username"],
            first_name=demo["first_name"],
        )

    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram authentication required",
        )

    user_data = validate_telegram_init_data(x_telegram_init_data)
    return await user_service.get_or_create(
        session,
        telegram_id=user_data["id"],
        username=user_data.get("username"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
    )
