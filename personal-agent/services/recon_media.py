"""Download social media, transcribe, translate for recon notifications."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from services.recon_providers import ContentItem
from services.translator import translator_service
from services.ytdlp_cmd import ytdlp_command

logger = logging.getLogger(__name__)

_MAX_VIDEO_BYTES = 48 * 1024 * 1024


async def _run_ytdlp_download(url: str, out_dir: Path) -> Path | None:
    out_template = str(out_dir / "%(id)s.%(ext)s")
    cmd = ytdlp_command(
        "-f",
        "best[filesize<?48M]/best",
        "--no-playlist",
        "--no-warnings",
        "-o",
        out_template,
        url,
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except Exception:
        logger.exception("yt-dlp download failed for %s", url)
        return None

    if proc.returncode != 0:
        logger.warning("yt-dlp download exit %s: %s", proc.returncode, stderr.decode()[:300])
        return None

    files = sorted(out_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files:
        if path.is_file() and path.stat().st_size <= _MAX_VIDEO_BYTES:
            return path
    return files[0] if files else None


async def _transcribe_path(path: Path) -> str | None:
    from config import settings
    from openai import AsyncOpenAI

    if not settings.openai_api_key:
        return None
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        with path.open("rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model=settings.openai_whisper_model,
                file=audio_file,
            )
        text = (response.text or "").strip()
        return text or None
    except Exception:
        logger.exception("Whisper transcription failed for %s", path)
        return None


def _is_mostly_non_russian(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if "a" <= c.lower() <= "z")
    cyrillic = sum(1 for c in letters if "\u0400" <= c <= "\u04ff")
    return latin > cyrillic * 1.5


async def enrich_content_item(
    item: ContentItem,
    *,
    user_translate_lang: str = "ru",
    download_media: bool = True,
) -> ContentItem:
    """Add transcription, translation, and optional local media file."""
    text_parts = [item.text] if item.text else []

    media_path: Path | None = None
    if download_media and item.page_url and item.media_type in ("video", "photo", None):
        tmp_dir = Path(tempfile.mkdtemp(prefix="recon_media_"))
        try:
            if "tiktok" in (item.page_url or ""):
                media_path = await _run_ytdlp_download(item.page_url, tmp_dir)
                if media_path:
                    item.media_path = str(media_path)
                    item.media_type = "video" if media_path.suffix.lower() in {".mp4", ".webm", ".mov"} else "photo"
                    if media_path.suffix.lower() in {".mp4", ".webm", ".mov", ".m4a", ".mp3"}:
                        transcript = await _transcribe_path(media_path)
                        if transcript:
                            text_parts.append(transcript)
        except Exception:
            logger.exception("Media download failed for %s", item.page_url)

    combined = "\n".join(p for p in text_parts if p.strip()).strip()
    if not combined:
        combined = item.text or ""

    if combined and translator_service.available and _is_mostly_non_russian(combined):
        result = await translator_service.translate(
            combined,
            "ru",
            user_preferred_lang=user_translate_lang,
        )
        if result and result.translated_text:
            item.translated_text = result.translated_text
            item.text = f"{combined}\n\n🌐 {result.translated_text}"
        else:
            item.text = combined
    else:
        item.text = combined

    return item


def cleanup_media_item(item: ContentItem) -> None:
    if not item.media_path:
        return
    path = Path(item.media_path)
    parent = path.parent
    try:
        if path.exists():
            path.unlink()
        if parent.name.startswith("recon_media_") and parent.exists():
            for child in parent.iterdir():
                child.unlink(missing_ok=True)
            parent.rmdir()
    except Exception:
        logger.debug("Could not cleanup media temp %s", item.media_path)
