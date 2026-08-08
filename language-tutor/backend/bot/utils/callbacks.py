"""Helpers for safe CallbackQuery replies.

`CallbackQuery.message` is None for inline messages and an `InaccessibleMessage`
for chats older than 48 hours. Calling edit_text/answer on those raises and
leaves the inline button spinning forever.
"""

from aiogram.types import CallbackQuery, InaccessibleMessage, InlineKeyboardMarkup, Message


def usable_message(callback: CallbackQuery) -> Message | None:
    message = callback.message
    if message is None or isinstance(message, InaccessibleMessage):
        return None
    return message


async def edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Edit the source message, falling back to a new message in the chat."""
    message = usable_message(callback)
    if message is not None:
        await message.edit_text(text, reply_markup=reply_markup)
        return
    if callback.bot and callback.from_user:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=reply_markup
        )


async def send_reply(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Send a new message in response to a callback."""
    message = usable_message(callback)
    if message is not None:
        await message.answer(text, reply_markup=reply_markup)
        return
    if callback.bot and callback.from_user:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=reply_markup
        )
