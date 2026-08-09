from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import vocab_rating_keyboard
from bot.utils.callbacks import edit_or_send, usable_message
from database.models import VocabularyCard
from services.user_service import user_service
from services.vocabulary_service import vocabulary_service

router = Router()


def _format_card(card: VocabularyCard) -> str:
    lines = [
        f"<b>{card.word}</b>",
        f"Перевод: {card.translation}",
    ]
    if card.example:
        lines.append(f"Пример: <i>{card.example}</i>")
    lines.append("\nКак вспомнили? Оцените честно — так FSRS подстроит интервал.")
    return "\n".join(lines)


async def _send_review_session(message: Message, session: AsyncSession, user_id: int) -> None:
    user = await user_service.get_by_telegram_id(session, user_id)
    if not user or not user.is_onboarded:
        await message.answer("Сначала пройди онбординг: /start")
        return

    due = await vocabulary_service.count_due(session, user)
    total = await vocabulary_service.count_total(session, user)

    if total == 0:
        await message.answer(
            "📚 Словарь пуст.\n\n"
            "После урока (2+ реплики) нажмите «Итоги урока» — слова добавятся сами. "
            "Или попросите в чате: «дай 5 слов на тему …»"
        )
        return

    if due == 0:
        await message.answer(
            f"✅ На сегодня всё!\n\n"
            f"В словаре {total} слов. Следующие повторы — когда FSRS назначит."
        )
        return

    card = await vocabulary_service.get_next_due(session, user)
    if not card:
        await message.answer("На сегодня повторений нет.")
        return

    await message.answer(
        f"📚 Повторение · осталось ~{due}\n\n{_format_card(card)}",
        reply_markup=vocab_rating_keyboard(card.id),
    )


@router.message(Command("review", "vocab"))
async def cmd_review(message: Message, session: AsyncSession) -> None:
    await _send_review_session(message, session, message.from_user.id)


@router.callback_query(F.data == "menu:review")
async def menu_review(callback: CallbackQuery, session: AsyncSession) -> None:
    target = usable_message(callback)
    await callback.answer()
    if target is not None:
        await _send_review_session(target, session, callback.from_user.id)


@router.callback_query(F.data.startswith("vocab:rate:"))
async def vocab_rate(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Ошибка")
        return

    try:
        card_id = int(parts[2])
        rating_value = int(parts[3])
    except ValueError:
        await callback.answer("Ошибка")
        return

    user = await user_service.get_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("Нужен /start")
        return

    stmt = select(VocabularyCard).where(
        VocabularyCard.id == card_id,
        VocabularyCard.user_id == user.id,
    )
    card = (await session.execute(stmt)).scalar_one_or_none()
    if not card:
        await callback.answer("Карточка не найдена")
        return

    await vocabulary_service.review(session, card, rating_value)
    await session.commit()

    remaining = await vocabulary_service.count_due(session, user)
    if remaining > 0:
        next_card = await vocabulary_service.get_next_due(session, user)
        if next_card:
            await edit_or_send(
                callback,
                f"📚 Повторение · осталось ~{remaining}\n\n{_format_card(next_card)}",
                reply_markup=vocab_rating_keyboard(next_card.id),
            )
        await callback.answer("Записано ✓")
        return

    total = await vocabulary_service.count_total(session, user)
    await edit_or_send(
        callback,
        f"🎉 Сессия завершена!\n\n"
        f"Все слова на сегодня повторены. В словаре {total} слов.",
    )
    await callback.answer("Готово!")
