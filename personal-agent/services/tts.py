from __future__ import annotations

import io
import tempfile
from pathlib import Path

import edge_tts

from config import settings


async def synthesize_voice(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, settings.tts_voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()


async def synthesize_voice_file(text: str) -> Path:
    audio = await synthesize_voice(text)
    tmp = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    tmp.write(audio)
    tmp.close()
    return Path(tmp.name)
