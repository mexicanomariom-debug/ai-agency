from __future__ import annotations

import logging

from aiohttp import web
from aiogram import Bot
from sqlalchemy import select

from config import settings
from database.models import User
from database.session import async_session_factory
from services.google_calendar import google_calendar_service

logger = logging.getLogger(__name__)


async def google_oauth_callback(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    code = request.query.get("code")
    state = request.query.get("state")
    error = request.query.get("error")

    if error:
        return web.Response(text=f"Ошибка авторизации: {error}", content_type="text/html; charset=utf-8")

    if not code or not state or not state.isdigit():
        return web.Response(text="Некорректный ответ OAuth", content_type="text/html; charset=utf-8")

    telegram_id = int(state)
    refresh_token = await google_calendar_service.exchange_code(code)
    if not refresh_token:
        return web.Response(text="Не удалось получить токен Google", content_type="text/html; charset=utf-8")

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return web.Response(text="Пользователь не найден", content_type="text/html; charset=utf-8")
        user.google_refresh_token = refresh_token
        user.google_calendar_enabled = True
        await session.commit()

    try:
        await bot.send_message(
            telegram_id,
            "✅ Google Calendar подключён! Новые задачи будут синхронизироваться автоматически.",
        )
    except Exception:
        logger.exception("Failed to notify user %s about calendar connect", telegram_id)

    return web.Response(
        text="<h2>Google Calendar подключён!</h2><p>Можете вернуться в Telegram.</p>",
        content_type="text/html; charset=utf-8",
    )


def create_oauth_app(bot: Bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/oauth/google/callback", google_oauth_callback)
    return app


async def start_oauth_server(bot: Bot) -> web.AppRunner | None:
    if not google_calendar_service.available:
        return None
    app = create_oauth_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.oauth_server_port)
    await site.start()
    logger.info("OAuth server listening on port %s", settings.oauth_server_port)
    return runner
