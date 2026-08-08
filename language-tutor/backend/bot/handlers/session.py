"""End-of-lesson recap: CEFR estimate, strengths and vocabulary import.

Previously this only ran from the removed voice Mini App, so Telegram users
never got a CEFR estimate or automatic FSRS words from their lessons.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.callbacks import usable_message
from services.personas import persona_service
from services.session_assessment import session_assessment_service
from services.user_service import user_service

router = Router()


async def _finish_lesson(message: Message, session: AsyncSession, telegram_id: int) -> None:
    user = await user_service.get_by_telegram_id(session, telegram_id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return

    persona = await persona_service.get_default(session)
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        result = await session_assessment_service.assess_voice_session(session, user, persona)
    except Exception:
        await message.answer("Не получилось подвести итоги. Попробуйте ещё раз чуть позже.")
        return

    if not result.assessed:
        if result.skipped_reason == "need_more_practice":
            await message.answer(
                "Пока мало материала для оценки. Поговорите со мной ещё немного "
                "(голосом или текстом) и снова нажмите «Итоги урока»."
            )
        else:
            await message.answer("Оценка недоступна: на сервере не настроен LLM.")
        return

    lines = ["✅ <b>Итоги урока</b>"]
    if result.speaking_cefr:
        lines.append(f"Уровень речи: <b>CEFR {result.speaking_cefr}</b>")
        if result.level_updated:
            lines.append("Профиль обновлён ✓")
    if result.summary:
        lines.append(f"\n{result.summary}")
    if result.strengths:
        lines.append("\n💪 <b>Сильные стороны</b>")
        lines.extend(f"• {item}" for item in result.strengths)
    if result.weaknesses:
        lines.append("\n🎯 <b>Над чем поработать</b>")
        lines.extend(f"• {item}" for item in result.weaknesses)
    if result.recommendation:
        lines.append(f"\n👉 {result.recommendation}")
    if result.words_added:
        lines.append(f"\n📚 Добавлено слов в повторение: <b>{result.words_added}</b> — /review")

    await message.answer("\n".join(lines))


@router.message(Command("finish"))
async def cmd_finish(message: Message, session: AsyncSession) -> None:
    await _finish_lesson(message, session, message.from_user.id)


@router.callback_query(F.data == "menu:finish")
async def menu_finish(callback: CallbackQuery, session: AsyncSession) -> None:
    target = usable_message(callback)
    await callback.answer()
    if target is not None:
        await _finish_lesson(target, session, callback.from_user.id)
