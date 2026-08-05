#!/usr/bin/env python3
"""Extract FGOS PDFs and ingest chunks into knowledge_chunks for RAG."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader
from sqlalchemy import delete, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.enums import Language
from database.models import KnowledgeChunk
from database.session import async_session_factory
from scripts.textbook_utils import (
    MANIFEST_PATH,
    RAW_DIR,
    TextChunk,
    chunk_text,
    level_for_grade,
    split_by_grade_sections,
)
from services.openai_service import openai_service


def extract_pdf_text(pdf_path: Path, pages: list[int] | None = None) -> str:
    reader = PdfReader(str(pdf_path))
    page_indices = pages or list(range(len(reader.pages)))
    parts: list[str] = []
    for idx in page_indices:
        if 0 <= idx < len(reader.pages):
            text = reader.pages[idx].extract_text() or ""
            parts.append(text)
    return "\n".join(parts)


def build_chunks_from_source(source: dict, raw_dir: Path) -> list[TextChunk]:
    pdf_path = raw_dir / f"{source['id']}.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"Missing PDF: {pdf_path} — run download_textbooks.py first")

    pages = source.get("pages")
    # manifest pages are 1-based for humans; convert to 0-based
    page_range = [p - 1 for p in pages] if pages else None
    text = extract_pdf_text(pdf_path, page_range)

    language = Language(source["language"])
    grades: list[int] = source["grades"]
    source_id = source["id"]
    title = source["title"]

    result: list[TextChunk] = []

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
    parser = argparse.ArgumentParser(description="Ingest FGOS materials into RAG database")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--clear", action="store_true", help="Clear knowledge_chunks before ingest")
    parser.add_argument("--no-embed", action="store_true", help="Store chunks without embeddings")
    args = parser.parse_args()

    with args.manifest.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    all_chunks: list[TextChunk] = []
    seen_ids: set[str] = set()
    for source in data["sources"]:
        sid = source["id"]
        if sid in seen_ids:
            continue
        seen_ids.add(sid)
        print(f"Parsing {sid} …")
        all_chunks.extend(build_chunks_from_source(source, args.raw_dir))

    print(f"Parsed {len(all_chunks)} chunks from {len(seen_ids)} PDF(s)")

    if args.no_embed:
        print("--no-embed: skipping database write")
        return

    asyncio.run(ingest(all_chunks, clear_existing=args.clear))


if __name__ == "__main__":
    main()
