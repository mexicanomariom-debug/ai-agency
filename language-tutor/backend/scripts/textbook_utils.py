"""Utilities for FGOS textbook download and RAG ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from database.enums import Language, ProficiencyLevel
from database.grade_mapping import GRADE_TO_LEVEL

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "textbooks" / "manifest.yaml"
MANIFEST_ADULTS_PATH = Path(__file__).resolve().parent.parent / "data" / "textbooks" / "manifest_adults.yaml"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "textbooks" / "raw"
ALL_MANIFESTS = (MANIFEST_PATH, MANIFEST_ADULTS_PATH)

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 200

GRADE_HEADER_RE = re.compile(
    r"(?:^|\n)\s*(?:\d+\.\s*)?(\d{1,2})\s*класс\b",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class TextChunk:
    language: Language
    level: ProficiencyLevel
    grade: int | None
    topic: str
    content: str
    source_id: str


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if len(c) > 80]


def split_by_grade_sections(text: str, grades: list[int]) -> dict[int, str]:
    """Split FRP text into per-grade sections using «N класс» headers."""
    matches = list(GRADE_HEADER_RE.finditer(text))
    if not matches:
        return {g: text for g in grades}

    sections: dict[int, str] = {}
    for i, match in enumerate(matches):
        grade = int(match.group(1))
        if grade not in grades:
            continue
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[grade] = text[start:end].strip()

    if not sections:
        return {g: text for g in grades}
    return sections


def level_for_grade(grade: int) -> ProficiencyLevel:
    return GRADE_TO_LEVEL.get(grade, ProficiencyLevel.INTERMEDIATE)