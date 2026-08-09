from __future__ import annotations

import html


def h(text: str | None) -> str:
    """Escape text for Telegram HTML parse mode."""
    if not text:
        return ""
    return html.escape(str(text), quote=False)


def bold(text: str | None) -> str:
    """Bold text for Telegram HTML."""
    return f"<b>{h(text)}</b>"


escape = h
