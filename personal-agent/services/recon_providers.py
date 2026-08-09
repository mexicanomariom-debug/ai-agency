"""Fetch content from monitored sources for Разведка и Вериф."""

from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlparse

import httpx

from database.models import ReconSourceType

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


@dataclass
class FetchResult:
    title: str
    content: str
    content_hash: str


def _normalize_text(text: str, *, limit: int = 4000) -> str:
    text = unescape(_TAG_RE.sub(" ", text))
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


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
    if "instagram.com" in lowered:
        return ReconSourceType.INSTAGRAM.value
    if "tiktok.com" in lowered:
        return ReconSourceType.TIKTOK.value
    if lowered.startswith("http") or "." in lowered:
        return ReconSourceType.WEBSITE.value
    return None


def _parse_source_input(text: str, source_type: str | None = None) -> tuple[str, str, str | None]:
    """Return (source_type, url_or_handle, label)."""
    raw = text.strip()
    label = None
    if "|" in raw:
        raw, label_part = [p.strip() for p in raw.split("|", 1)]
        label = label_part or None

    detected = source_type or _detect_source_type(raw)
    if not detected:
        detected = ReconSourceType.WEBSITE.value

    if detected == ReconSourceType.ECON_CALENDAR.value:
        return detected, "ff_calendar_thisweek", label or "Экономический календарь"

    if detected == ReconSourceType.TELEGRAM.value:
        handle = _normalize_telegram_handle(raw)
        return detected, handle, label or f"@{handle}"

    return detected, raw, label



async def fetch_source_content(source_type: str, url_or_handle: str) -> FetchResult | None:
    fetchers = {
        ReconSourceType.WEBSITE.value: _fetch_website,
        ReconSourceType.TELEGRAM.value: _fetch_telegram,
        ReconSourceType.INSTAGRAM.value: _fetch_social_stub,
        ReconSourceType.TIKTOK.value: _fetch_social_stub,
        ReconSourceType.ECON_CALENDAR.value: _fetch_econ_calendar,
    }
    fetcher = fetchers.get(source_type)
    if not fetcher:
        return None
    return await fetcher(url_or_handle)


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
    return FetchResult(title=title, content=content, content_hash=_hash_content(content))


def _parse_rss(body: str, source: str) -> FetchResult | None:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None

    items: list[str] = []
    title = source
    channel = root.find("channel")
    if channel is not None:
        ch_title = channel.findtext("title")
        if ch_title:
            title = ch_title.strip()
        for item in channel.findall("item")[:8]:
            parts = [item.findtext("title") or "", item.findtext("description") or ""]
            items.append(" — ".join(p.strip() for p in parts if p and p.strip()))
    else:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        feed_title = root.findtext("a:title", default="", namespaces=ns)
        if feed_title:
            title = feed_title.strip()
        for entry in root.findall("a:entry", ns)[:8]:
            parts = [
                entry.findtext("a:title", default="", namespaces=ns),
                entry.findtext("a:summary", default="", namespaces=ns),
            ]
            items.append(" — ".join(p.strip() for p in parts if p and p.strip()))

    content = _normalize_text("\n".join(items))
    if not content:
        return None
    return FetchResult(title=title, content=content, content_hash=_hash_content(content))


async def _fetch_telegram(handle: str) -> FetchResult | None:
    channel = _normalize_telegram_handle(handle)
    if not channel:
        return None
    url = f"https://t.me/s/{channel}"
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            html = resp.text
    except Exception:
        logger.exception("Telegram fetch failed for %s", handle)
        return None

    messages = re.findall(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        html,
        re.S | re.I,
    )
    if not messages:
        # Fallback: strip tags from whole page preview area
        block = re.search(r'tgme_channel_history.*?tgme_footer', html, re.S | re.I)
        if block:
            content = _normalize_text(block.group(0))
            if len(content) > 80:
                return FetchResult(
                    title=f"Telegram @{channel}",
                    content=content,
                    content_hash=_hash_content(content),
                )
        logger.warning("Telegram channel @%s: no messages in HTML", channel)
        return None

    texts = [_normalize_text(m, limit=500) for m in messages[-6:]]
    content = "\n".join(t for t in texts if t)
    if not content:
        return None
    return FetchResult(
        title=f"Telegram @{channel}",
        content=content,
        content_hash=_hash_content(content),
    )


async def _fetch_social_stub(url: str) -> FetchResult | None:
    """Instagram/TikTok need official API — return profile URL marker for manual verify."""
    target = url.strip()
    if not target.startswith("http"):
        target = f"https://{target}"
    content = f"Мониторинг {target}: публичный API недоступен. Перешлите пост боту для верификации."
    return FetchResult(
        title=urlparse(target).netloc or target,
        content=content,
        content_hash=_hash_content(target),
    )


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

    lines: list[str] = []
    for event in root.findall(".//event")[:30]:
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
            lines.append(line)

    content = _normalize_text("\n".join(lines))
    if not content:
        return None
    return FetchResult(
        title="Экономический календарь (неделя)",
        content=content,
        content_hash=_hash_content(content),
    )
