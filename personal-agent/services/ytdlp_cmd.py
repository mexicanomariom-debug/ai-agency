"""Shared yt-dlp command helper."""

from __future__ import annotations

import shutil
import sys


def ytdlp_command(*args: str) -> list[str]:
    if shutil.which("yt-dlp"):
        return ["yt-dlp", *args]
    return [sys.executable, "-m", "yt_dlp", *args]
