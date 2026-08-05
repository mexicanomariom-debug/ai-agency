#!/usr/bin/env python3
"""Download FGOS textbook / FRP PDFs listed in manifest.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.textbook_utils import MANIFEST_PATH, RAW_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Download FGOS materials for RAG")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    with args.manifest.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    args.output.mkdir(parents=True, exist_ok=True)
    url_cache: dict[str, Path] = {}

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        for source in data["sources"]:
            source_id = source["id"]
            url = source["url"]
            dest = args.output / f"{source_id}.pdf"

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

    print(f"\nDone. {len(url_cache)} unique PDF(s), {len(data['sources'])} files in {args.output}")


if __name__ == "__main__":
    main()
