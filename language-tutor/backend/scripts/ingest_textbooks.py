#!/usr/bin/env python3
"""Extract textbooks / phrasebooks and ingest chunks into knowledge_chunks for RAG."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader
from sqlalchemy import delete, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.enums import Language, ProficiencyLevel
from database.models import KnowledgeChunk
from database.session import async_session_factory
from scripts.textbook_utils import (
    ALL_MANIFESTS,
    MANIFEST_PATH,
    RAW_DIR,
    TextChunk,
    chunk_text,
    level_for_grade,
    split_by_grade_sections,
)
from services.openai_service import openai_service


def _file_ext(source: dict) -> str:
    return "txt" if source.get("format") == "txt" else "pdf"


def extract_pdf_text(pdf_path: Path, pages: list[int] | None = None) -> str:
    reader = PdfReader(str(pdf_path))
    page_indices = pages or list(range(len(reader.pages)))
    parts: list[str] = []
    for idx in page_indices:
        if 0 <= idx < len(reader.pages):
            parts.append(reader.pages[idx].extract_text() or "")
    return "\n".join(parts)


def load_source_text(source: dict, raw_dir: Path) -> str:
    ext = _file_ext(source)
    path = raw_dir / f"{source['id']}.{ext}"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path} — run download_textbooks.py --all first")

    if ext == "txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    pages = source.get("pages")
    page_range = [p - 1 for p in pages] if pages else None
    return extract_pdf_text(path, page_range)


def build_chunks_from_source(source: dict, raw_dir: Path) -> list[TextChunk]:
    text = load_source_text(source, raw_dir)
    language = Language(source["language"])
    source_id = source["id"]
    title = source["title"]
    result: list[TextChunk] = []

    if source.get("audience") == "adult":
        levels = [ProficiencyLevel(lvl) for lvl in source.get("levels", ["intermediate"])]
        primary_level = levels[len(levels) // 2]
        for i, piece in enumerate(chunk_text(text)):
            result.append(
                TextChunk(
                    language=language,
                    level=primary_level,
                    grade=None,
                    topic=f"{title} (часть {i + 1})",
                    content=piece,
                    source_id=source_id,
                )
            )
        return result

    grades: list[int] = source["grades"]
    if source.get("split_by_grade"):
        sections = split_by_grade_sections(text, grades)
        for grade, section_text in sections.items():
            for i, piece in enumerate(chunk_text(section_text)):
                result.append(
                    TextChunk(
                        language=language,
                        level=level_for_grade(grade),
                        grade=grade,
                        topic=f"{title} — {grade} класс (часть {i + 1})",
                        content=piece,
                        source_id=source_id,
                    )
                )
    else:
        for grade in grades:
            for i, piece in enumerate(chunk_text(text)):
                result.append(
                    TextChunk(
                        language=language,
                        level=level_for_grade(grade),
                        grade=grade,
                        topic=f"{title} — {grade} класс (часть {i + 1})",
                        content=piece,
                        source_id=source_id,
                    )
                )

    return result


async def ingest(chunks: list[TextChunk], *, clear_existing: bool) -> None:
    async with async_session_factory() as session:
        if clear_existing:
            await session.execute(delete(KnowledgeChunk))
            await session.commit()
            print("Cleared existing knowledge_chunks")

        existing = await session.execute(select(KnowledgeChunk.topic))
        existing_topics = {row[0] for row in existing.all()}

        added = 0
        for chunk in chunks:
            if chunk.topic in existing_topics:
                continue

            embedding = await openai_service.create_embedding(chunk.content)
            session.add(
                KnowledgeChunk(
                    language=chunk.language,
                    level=chunk.level,
                    grade=chunk.grade,
                    topic=chunk.topic,
                    content=chunk.content,
                    embedding=embedding,
                )
            )
            existing_topics.add(chunk.topic)
            added += 1
            if added % 20 == 0:
                await session.commit()
                print(f"  … {added} chunks ingested")

        await session.commit()
        print(f"Ingested {added} new chunks ({len(chunks)} total parsed)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest FGOS and adult materials into RAG database")
    parser.add_argument("--manifest", type=Path, action="append", dest="manifests")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--clear", action="store_true", help="Clear knowledge_chunks before ingest")
    parser.add_argument("--no-embed", action="store_true", help="Parse only, skip DB write")
    parser.add_argument("--all", action="store_true", help="Ingest school + adult manifests")
    args = parser.parse_args()

    manifests = args.manifests or ([*ALL_MANIFESTS] if args.all else [MANIFEST_PATH])

    all_chunks: list[TextChunk] = []
    seen_ids: set[str] = set()
    for manifest in manifests:
        with manifest.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for source in data["sources"]:
            sid = source["id"]
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            print(f"Parsing {sid} …")
            all_chunks.extend(build_chunks_from_source(source, args.raw_dir))

    print(f"Parsed {len(all_chunks)} chunks from {len(seen_ids)} source(s)")

    if args.no_embed:
        print("--no-embed: skipping database write")
        return

    asyncio.run(ingest(all_chunks, clear_existing=args.clear))


if __name__ == "__main__":
    main()
