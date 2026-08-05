#!/usr/bin/env python3
"""Download FGOS textbooks and adult phrasebooks listed in manifest YAML files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.textbook_utils import ALL_MANIFESTS, MANIFEST_PATH, RAW_DIR


def _file_ext(source: dict) -> str:
    fmt = source.get("format", "pdf")
    return "txt" if fmt == "txt" else "pdf"


def download_manifest(manifest_path: Path, output: Path, client: httpx.Client, url_cache: dict[str, Path]) -> int:
    with manifest_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for source in data["sources"]:
        source_id = source["id"]
        url = source["url"]
        ext = _file_ext(source)
        dest = output / f"{source_id}.{ext}"

        if url in url_cache:
            cached = url_cache[url]
            dest.write_bytes(cached.read_bytes())
            print(f"copy {cached.name} -> {dest.name}")
            continue

        print(f"Downloading {source_id} …")
        response = client.get(url)
        response.raise_for_status()
        dest.write_bytes(response.content)
        url_cache[url] = dest
        print(f"  -> {dest} ({len(response.content) // 1024} KB)")

    return len(data["sources"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Download FGOS and adult phrasebook materials for RAG")
    parser.add_argument("--manifest", type=Path, action="append", dest="manifests")
    parser.add_argument("--output", type=Path, default=RAW_DIR)
    parser.add_argument("--all", action="store_true", help="Download school + adult manifests")
    args = parser.parse_args()

    manifests = args.manifests or ([*ALL_MANIFESTS] if args.all else [MANIFEST_PATH])
    args.output.mkdir(parents=True, exist_ok=True)
    url_cache: dict[str, Path] = {}
    total = 0

    with httpx.Client(
        timeout=120.0,
        follow_redirects=True,
        headers={"User-Agent": "Opus5LanguageTutor/1.0 (educational; RAG indexing)"},
    ) as client:
        for manifest in manifests:
            print(f"\n=== {manifest.name} ===")
            total += download_manifest(manifest, args.output, client, url_cache)

    print(f"\nDone. {len(url_cache)} unique URL(s), {total} files in {args.output}")


if __name__ == "__main__":
    main()
