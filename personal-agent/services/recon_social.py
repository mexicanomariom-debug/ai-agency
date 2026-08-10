"""Fetchers for social sources: TikTok, Twitter/X, Facebook, WhatsApp, Instagram."""

from __future__ import annotations

import json
import logging
import re
from html import unescape
from urllib.parse import urlparse

import httpx

from config import settings
from services.recon_providers import ContentItem, FetchResult, _build_result, _hash_content, _item_id, _normalize_text

logger = logging.getLogger(__name__)

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_at(value: str) -> str:
    return value.strip().lstrip("@")


def _ensure_url(value: str, default_host: str) -> str:
    value = value.strip()
    if value.startswith("http"):
        return value
    if value.startswith("www."):
        return f"https://{value}"
    return f"https://{default_host}/{_strip_at(value)}"


def normalize_tiktok_handle(value: str) -> str:
    value = value.strip()
    if "tiktok.com" in value:
        match = re.search(r"tiktok\.com/@?([^/?#]+)", value, re.I)
        return match.group(1) if match else value
    return _strip_at(value)


def normalize_twitter_handle(value: str) -> str:
    value = value.strip()
    for pattern in (r"(?:twitter|x)\.com/([^/?#]+)", r"^@?([\w_]+)$"):
        match = re.search(pattern, value, re.I)
        if match:
            return match.group(1)
    return _strip_at(value)


def normalize_instagram_handle(value: str) -> str:
    value = value.strip()
    match = re.search(r"instagram\.com/([^/?#]+)", value, re.I)
    if match:
        return match.group(1)
    return _strip_at(value)


def normalize_facebook_page(value: str) -> str:
    value = value.strip()
    if "facebook.com" in value:
        match = re.search(r"facebook\.com/([^/?#]+)", value, re.I)
        return match.group(1) if match else value
    return value.lstrip("/")


def normalize_whatsapp_channel(value: str) -> str:
    value = value.strip()
    match = re.search(r"(?:whatsapp\.com|wa\.me)/channel/([^/?#]+)", value, re.I)
    if match:
        return match.group(1)
    if value.startswith("channel/"):
        return value.split("/", 1)[1]
    return value


async def _http_get(url: str, *, timeout: float = 25.0) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": _BROWSER_UA})
            resp.raise_for_status()
            return resp.text
    except Exception:
        logger.exception("HTTP fetch failed for %s", url)
        return None


async def _fetch_rss_items(feed_url: str, *, title: str, limit: int = 12) -> list[ContentItem]:
    from services.recon_providers import _parse_rss

    body = await _http_get(feed_url)
    if not body:
        return []
    parsed = _parse_rss(body, feed_url)
    if not parsed:
        return []
    items: list[ContentItem] = []
    for item in (parsed.items or [])[:limit]:
        page_url = None
        link_match = re.search(r"https?://\S+", item.text)
        if link_match:
            page_url = link_match.group(0)
        items.append(
            ContentItem(
                item_id=item.item_id,
                text=item.text,
                title=item.title,
                page_url=page_url,
                media_type="link",
            )
        )
    return items


async def _fetch_tiktok_ytdlp(handle: str) -> list[ContentItem]:
    import asyncio

    profile = normalize_tiktok_handle(handle)
    url = f"https://www.tiktok.com/@{profile}"
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--playlist-end",
        "12",
        url,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
    except Exception:
        logger.exception("yt-dlp TikTok failed for %s", url)
        return []

    if proc.returncode != 0:
        logger.warning("yt-dlp exit %s: %s", proc.returncode, stderr.decode()[:300])
        return []

    try:
        data = json.loads(stdout.decode())
    except json.JSONDecodeError:
        return []

    entries = data.get("entries") or [data]
    items: list[ContentItem] = []
    for entry in entries[:12]:
        if not isinstance(entry, dict):
            continue
        video_id = str(entry.get("id") or entry.get("display_id") or "")
        if not video_id:
            continue
        page_url = entry.get("webpage_url") or entry.get("url") or f"{url}/video/{video_id}"
        caption = (entry.get("title") or entry.get("description") or "").strip()
        if not caption:
            caption = f"TikTok #{video_id}"
        items.append(
            ContentItem(
                item_id=_item_id("tiktok", video_id),
                text=_normalize_text(caption, limit=800),
                title=_normalize_text(caption, limit=120),
                page_url=page_url,
                media_type="video",
            )
        )
    return items


async def fetch_tiktok(handle: str) -> FetchResult | None:
    profile = normalize_tiktok_handle(handle)
    items = await _fetch_tiktok_ytdlp(profile)
    if not items:
        # oEmbed fallback for single video URLs
        if "/video/" in handle:
            return await _fetch_tiktok_oembed(handle)
        return None
    return _build_result(f"TikTok @{profile}", items)


async def _fetch_tiktok_oembed(url: str) -> FetchResult | None:
    target = url if url.startswith("http") else f"https://{url}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                "https://www.tiktok.com/oembed",
                params={"url": target},
                headers={"User-Agent": _BROWSER_UA},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None
    title = (data.get("title") or "").strip()
    if not title:
        return None
    video_id = re.search(r"/video/(\d+)", target)
    item_id = _item_id("tiktok", video_id.group(1) if video_id else target)
    item = ContentItem(
        item_id=item_id,
        text=title,
        title=title[:120],
        page_url=target,
        media_type="video",
    )
    content = _normalize_text(title)
    return FetchResult(title="TikTok", content=content, content_hash=_hash_content(content), items=[item])


async def fetch_twitter(handle: str) -> FetchResult | None:
    user = normalize_twitter_handle(handle)
    base = settings.rsshub_base_url.rstrip("/")
    items = await _fetch_rss_items(f"{base}/twitter/user/{user}", title=f"Twitter @{user}")
    if items:
        return _build_result(f"Twitter @{user}", items)

    # Syndication fallback
    html = await _http_get(f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{user}")
    if not html:
        return None
    texts = re.findall(r'data-tweet-text="([^"]+)"', html)
    if not texts:
        texts = [_normalize_text(unescape(_TAG_RE.sub(" ", chunk)), limit=280) for chunk in re.findall(r'"full_text":"([^"]+)"', html)]
    items = []
    for idx, text in enumerate(texts[:12]):
        if not text:
            continue
        items.append(
            ContentItem(
                item_id=_item_id("twitter", user, text),
                text=text,
                title=text[:120],
                page_url=f"https://x.com/{user}",
                media_type="text",
            )
        )
    return _build_result(f"Twitter @{user}", items)


async def fetch_facebook(page: str) -> FetchResult | None:
    slug = normalize_facebook_page(page)
    base = settings.rsshub_base_url.rstrip("/")
    items = await _fetch_rss_items(f"{base}/facebook/page/{slug}", title=f"Facebook {slug}")
    if items:
        return _build_result(f"Facebook {slug}", items)

    html = await _http_get(_ensure_url(page, "facebook.com"))
    if not html:
        return None
    og = re.search(r'property="og:description" content="([^"]+)"', html)
    if not og:
        return None
    text = _normalize_text(unescape(og.group(1)), limit=800)
    item = ContentItem(item_id=_item_id("fb", slug, text), text=text, page_url=_ensure_url(page, "facebook.com"))
    return FetchResult(title=f"Facebook {slug}", content=text, content_hash=_hash_content(text), items=[item])


async def fetch_instagram(handle: str) -> FetchResult | None:
    user = normalize_instagram_handle(handle)
    base = settings.rsshub_base_url.rstrip("/")
    items = await _fetch_rss_items(f"{base}/instagram/user/{user}", title=f"Instagram @{user}")
    if items:
        for item in items:
            item.media_type = item.media_type or "photo"
        return _build_result(f"Instagram @{user}", items)

    html = await _http_get(f"https://www.instagram.com/{user}/")
    if not html:
        return None
    desc = re.search(r'"description":"([^"]+)"', html)
    if not desc:
        return None
    text = _normalize_text(unescape(desc.group(1)), limit=800)
    item = ContentItem(
        item_id=_item_id("ig", user, text),
        text=text,
        page_url=f"https://www.instagram.com/{user}/",
        media_type="photo",
    )
    return FetchResult(title=f"Instagram @{user}", content=text, content_hash=_hash_content(text), items=[item])


async def fetch_whatsapp(channel: str) -> FetchResult | None:
    channel_id = normalize_whatsapp_channel(channel)
    url = f"https://www.whatsapp.com/channel/{channel_id}"
    html = await _http_get(url)
    if not html:
        return None

    items: list[ContentItem] = []
    for block in re.findall(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', html, re.I):
        text = _normalize_text(unescape(block), limit=800)
        if len(text) > 20:
            items.append(
                ContentItem(
                    item_id=_item_id("wa", channel_id, text),
                    text=text,
                    page_url=url,
                    media_type="text",
                )
            )

    json_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    for raw in json_blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        posts = data if isinstance(data, list) else [data]
        for post in posts:
            if not isinstance(post, dict):
                continue
            text = _normalize_text(post.get("articleBody") or post.get("description") or "", limit=800)
            if text:
                items.append(
                    ContentItem(
                        item_id=_item_id("wa", channel_id, text),
                        text=text,
                        title=_normalize_text(post.get("headline") or "", limit=120) or None,
                        page_url=url,
                        media_type="text",
                    )
                )

    if not items:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = _normalize_text(title_match.group(1), limit=200) if title_match else channel_id
        text = f"WhatsApp канал: {title}"
        items.append(ContentItem(item_id=_item_id("wa", channel_id), text=text, page_url=url))

    return _build_result(f"WhatsApp {channel_id[:16]}…", items[:12])
