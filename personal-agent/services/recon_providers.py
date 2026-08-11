"""Fetch content from monitored sources for Разведка и Вериф."""

from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import urlparse

import httpx

from database.models import ReconSourceType

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_INTEREST_RE = re.compile(r"(?:\s|^)(?:интерес|interest)\s*:\s*(.+)$", re.I)


class FetchFailure(Exception):
    """Source content could not be loaded."""

    def __init__(self, reason: str, *, user_hint: str = "") -> None:
        self.reason = reason
        self.user_hint = user_hint
        super().__init__(user_hint or reason)


FETCH_REASON_LABELS = {
    "not_public": "не публичный канал",
    "network": "ошибка сети",
    "empty": "нет постов",
}


@dataclass
class ContentItem:
    item_id: str
    text: str
    title: str | None = None
    page_url: str | None = None
    media_type: str | None = None  # video, photo, text, link
    media_path: str | None = None
    translated_text: str | None = None


@dataclass
class FetchResult:
    title: str
    content: str
    content_hash: str
    items: list[ContentItem] = field(default_factory=list)


def _normalize_text(text: str, *, limit: int = 4000) -> str:
    text = unescape(_TAG_RE.sub(" ", text))
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _item_id(*parts: str) -> str:
    raw = "|".join(p.strip() for p in parts if p and p.strip())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_telegram_handle(value: str) -> str:
    value = value.strip()
    value = value.replace("https://", "").replace("http://", "")
    if value.startswith("t.me/"):
        value = value[5:]
    if value.startswith("@"):
        value = value[1:]
    if value.startswith("s/"):
        value = value[2:]
    return value.split("/")[0].split("?")[0]


def _detect_source_type(text: str) -> str | None:
    lowered = text.strip().lower()
    if lowered in ("auto", "календарь", "calendar", "эко", "эконом"):
        return ReconSourceType.ECON_CALENDAR.value
    if lowered.startswith("@") or "t.me/" in lowered or "telegram.me/" in lowered:
        return ReconSourceType.TELEGRAM.value
    if "whatsapp.com/channel" in lowered or lowered.startswith("channel/"):
        return ReconSourceType.WHATSAPP.value
    if "instagram.com" in lowered:
        return ReconSourceType.INSTAGRAM.value
    if "tiktok.com" in lowered:
        return ReconSourceType.TIKTOK.value
    if "twitter.com" in lowered or "x.com/" in lowered:
        return ReconSourceType.TWITTER.value
    if "facebook.com" in lowered or "fb.com" in lowered:
        return ReconSourceType.FACEBOOK.value
    if lowered.startswith("http") or "." in lowered:
        return ReconSourceType.WEBSITE.value
    return None


def _strip_interest_suffix(text: str) -> tuple[str, str | None]:
    match = _INTEREST_RE.search(text.strip())
    if not match:
        return text.strip(), None
    interest = match.group(1).strip()
    base = text[: match.start()].strip()
    return base, interest or None


def _parse_source_input(text: str, source_type: str | None = None) -> tuple[str, str, str | None, str | None]:
    """Return (source_type, url_or_handle, label, filter_query)."""
    raw = text.strip()
    raw, filter_query = _strip_interest_suffix(raw)

    label = None
    if "|" in raw:
        raw, label_part = [p.strip() for p in raw.split("|", 1)]
        label = label_part or None

    detected = source_type or _detect_source_type(raw)
    if not detected:
        detected = ReconSourceType.WEBSITE.value

    if detected == ReconSourceType.ECON_CALENDAR.value:
        return detected, "ff_calendar_thisweek", label or "Экономический календарь", filter_query

    if detected == ReconSourceType.TELEGRAM.value:
        handle = _normalize_telegram_handle(raw)
        return detected, handle, label or f"@{handle}", filter_query

    if detected == ReconSourceType.TIKTOK.value:
        from services.recon_social import normalize_tiktok_handle

        handle = normalize_tiktok_handle(raw)
        return detected, handle, label or f"@{handle}", filter_query

    if detected == ReconSourceType.TWITTER.value:
        from services.recon_social import normalize_twitter_handle

        handle = normalize_twitter_handle(raw)
        return detected, handle, label or f"@{handle}", filter_query

    if detected == ReconSourceType.INSTAGRAM.value:
        from services.recon_social import normalize_instagram_handle

        handle = normalize_instagram_handle(raw)
        return detected, handle, label or f"@{handle}", filter_query

    if detected == ReconSourceType.FACEBOOK.value:
        from services.recon_social import normalize_facebook_page

        page = normalize_facebook_page(raw)
        return detected, page, label or page, filter_query

    if detected == ReconSourceType.WHATSAPP.value:
        from services.recon_social import normalize_whatsapp_channel

        channel = normalize_whatsapp_channel(raw)
        return detected, channel, label or f"WA {channel[:12]}…", filter_query

    return detected, raw, label, filter_query


async def fetch_source_content(source_type: str, url_or_handle: str) -> FetchResult | None:
    from services.recon_social import (
        fetch_facebook,
        fetch_instagram,
        fetch_tiktok,
        fetch_twitter,
        fetch_whatsapp,
    )

    fetchers = {
        ReconSourceType.WEBSITE.value: _fetch_website,
        ReconSourceType.TELEGRAM.value: _fetch_telegram,
        ReconSourceType.INSTAGRAM.value: fetch_instagram,
        ReconSourceType.TIKTOK.value: fetch_tiktok,
        ReconSourceType.TWITTER.value: fetch_twitter,
        ReconSourceType.FACEBOOK.value: fetch_facebook,
        ReconSourceType.WHATSAPP.value: fetch_whatsapp,
        ReconSourceType.ECON_CALENDAR.value: _fetch_econ_calendar,
    }
    fetcher = fetchers.get(source_type)
    if not fetcher:
        return None
    try:
        return await fetcher(url_or_handle)
    except FetchFailure:
        raise


def _build_result(title: str, items: list[ContentItem]) -> FetchResult | None:
    if not items:
        return None
    content = "\n".join(item.text for item in items if item.text)
    content = _normalize_text(content)
    if not content:
        return None
    return FetchResult(
        title=title,
        content=content,
        content_hash=_hash_content(content),
        items=items,
    )


async def _fetch_website(url: str) -> FetchResult | None:
    target = url.strip()
    if not target.startswith("http"):
        target = f"https://{target}"
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(
                target,
                headers={"User-Agent": "PersonalAgentRecon/1.0"},
            )
            resp.raise_for_status()
            body = resp.text
    except Exception:
        logger.exception("Website fetch failed for %s", url)
        return None

    if "<rss" in body[:500].lower() or "<feed" in body[:500].lower():
        return _parse_rss(body, target)

    content = _normalize_text(body)
    if len(content) < 40:
        return None
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    title = _normalize_text(title_match.group(1), limit=200) if title_match else urlparse(target).netloc
    item = ContentItem(item_id=_item_id(target, content), text=content, title=title)
    return FetchResult(title=title, content=content, content_hash=_hash_content(content), items=[item])


def _parse_rss(body: str, source: str) -> FetchResult | None:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None

    items: list[ContentItem] = []
    title = source
    channel = root.find("channel")
    if channel is not None:
        ch_title = channel.findtext("title")
        if ch_title:
            title = ch_title.strip()
        for item in channel.findall("item")[:12]:
            parts = [item.findtext("title") or "", item.findtext("description") or ""]
            text = " — ".join(p.strip() for p in parts if p and p.strip())
            if not text:
                continue
            guid = item.findtext("guid") or item.findtext("link") or text
            items.append(
                ContentItem(
                    item_id=_item_id(source, guid),
                    text=_normalize_text(text, limit=800),
                    title=_normalize_text(parts[0], limit=200) if parts[0] else None,
                )
            )
    else:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        feed_title = root.findtext("a:title", default="", namespaces=ns)
        if feed_title:
            title = feed_title.strip()
        for entry in root.findall("a:entry", ns)[:12]:
            parts = [
                entry.findtext("a:title", default="", namespaces=ns),
                entry.findtext("a:summary", default="", namespaces=ns),
            ]
            text = " — ".join(p.strip() for p in parts if p and p.strip())
            if not text:
                continue
            link_el = entry.find("a:link", ns)
            link = link_el.get("href") if link_el is not None else text
            items.append(
                ContentItem(
                    item_id=_item_id(source, link),
                    text=_normalize_text(text, limit=800),
                    title=_normalize_text(parts[0], limit=200) if parts[0] else None,
                )
            )

    return _build_result(title, items)


async def _fetch_telegram(handle: str) -> FetchResult | None:
    import asyncio

    last_failure: FetchFailure | None = None
    for attempt in range(3):
        try:
            result = await _fetch_telegram_once(handle)
            if result:
                return result
        except FetchFailure as exc:
            last_failure = exc
            if exc.reason == "not_public":
                raise
        except Exception:
            logger.exception("Telegram fetch attempt %s failed for %s", attempt + 1, handle)
        if attempt < 2:
            await asyncio.sleep(1.5 * (attempt + 1))

    if last_failure:
        raise last_failure
    raise FetchFailure(
        "network",
        user_hint="Не удалось загрузить канал. Попробуйте позже.",
    )


def _telegram_not_public(html: str, channel: str) -> bool:
    if "tgme_widget_message" in html:
        return False
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = _normalize_text(title_match.group(1), limit=200) if title_match else ""
    if re.search(rf"Contact @{re.escape(channel)}", title, re.I):
        return True
    if "tgme_page_photo" in html and "tgme_channel_info" not in html:
        return True
    return False


async def _fetch_telegram_once(handle: str) -> FetchResult | None:
    channel = _normalize_telegram_handle(handle)
    if not channel:
        raise FetchFailure("empty", user_hint="Укажите имя канала, например @channelname")

    url = f"https://t.me/s/{channel}"
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
                },
            )
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        logger.exception("Telegram fetch failed for %s", handle)
        raise FetchFailure(
            "network",
            user_hint=f"Сеть: не удалось открыть t.me/s/{channel}",
        ) from exc

    if _telegram_not_public(html, channel):
        raise FetchFailure(
            "not_public",
            user_hint=(
                f"@{channel} — не публичный канал с постами.\n"
                "Нужен канал с превью на t.me/s/имя (не личный профиль и не приватный чат)."
            ),
        )

    items: list[ContentItem] = []
    for post_id, raw_html in re.findall(
        r'data-post="([^"]+)"[^>]*>.*?tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        html,
        re.S | re.I,
    ):
        text = _normalize_text(raw_html, limit=800)
        if text:
            items.append(ContentItem(item_id=_item_id("tg", post_id), text=text))

    if not items:
        messages = re.findall(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            html,
            re.S | re.I,
        )
        for raw_html in messages[-12:]:
            text = _normalize_text(raw_html, limit=800)
            if text:
                items.append(ContentItem(item_id=_item_id("tg", channel, text), text=text))

    if not items:
        block = re.search(r"tgme_channel_history.*?tgme_footer", html, re.S | re.I)
        if block:
            content = _normalize_text(block.group(0))
            if len(content) > 80:
                item = ContentItem(item_id=_item_id("tg", channel, content), text=content)
                return FetchResult(
                    title=f"Telegram @{channel}",
                    content=content,
                    content_hash=_hash_content(content),
                    items=[item],
                )
        logger.warning("Telegram channel @%s: no messages in HTML", channel)
        raise FetchFailure(
            "empty",
            user_hint=f"@{channel}: посты не найдены (канал пуст или закрыт).",
        )

    return _build_result(f"Telegram @{channel}", items)


async def _fetch_econ_calendar(_: str) -> FetchResult | None:
    """ForexFactory weekly calendar (free XML, no API key)."""
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
    except Exception:
        logger.exception("Economic calendar fetch failed")
        return None

    items: list[ContentItem] = []
    for event in root.findall(".//event")[:40]:
        parts = [
            event.findtext("title") or "",
            event.findtext("country") or "",
            event.findtext("date") or "",
            event.findtext("impact") or "",
            event.findtext("forecast") or "",
            event.findtext("previous") or "",
        ]
        line = " | ".join(p.strip() for p in parts if p and p.strip())
        if line:
            items.append(
                ContentItem(
                    item_id=_item_id("econ", parts[0] or "", parts[2] or ""),
                    text=_normalize_text(line, limit=400),
                    title=_normalize_text(parts[0], limit=120) if parts[0] else None,
                )
            )

    return _build_result("Экономический календарь (неделя)", items)
