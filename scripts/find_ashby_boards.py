#!/usr/bin/env python
"""Discover Ashby job boards from a list of company URLs.

Example:
    python scripts/find_ashby_boards.py --input urls.txt

The script fetches each URL, looks for pattern 'jobs.ashbyhq.com/<board>',
and appends new boards into 'jd_filter/sources/ashby_boards.json'.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Set

import httpx
from tqdm.asyncio import tqdm

BOARDS_FILE = Path(__file__).resolve().parent.parent / "jd_filter" / "sources" / "ashby_boards.json"

ASYNC_SEMAPHORE = asyncio.Semaphore(20)
PATTERN = re.compile(r"jobs\.ashbyhq\.com/([A-Za-z0-9\-]+)")

def load_boards() -> Set[str]:
    if BOARDS_FILE.exists():
        try:
            return set(json.loads(BOARDS_FILE.read_text()).keys())
        except Exception:
            return set()
    return set()

def save_boards(boards: Set[str]) -> None:
    data = {b: {"fails": 0} for b in sorted(boards)}
    BOARDS_FILE.write_text(json.dumps(data, indent=2))

async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    try:
        async with ASYNC_SEMAPHORE:
            r = await client.get(url, timeout=10)
            r.raise_for_status()
            return r.text
    except Exception:
        return ""

async def crawl(urls: list[str]) -> Set[str]:
    boards: Set[str] = set()
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for html in tqdm.as_completed([fetch_html(client, u) for u in urls], total=len(urls)):
            content = await html
            for match in PATTERN.finditer(content):
                boards.add(match.group(1))
    return boards

def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Discover Ashby board names from company URLs")
    parser.add_argument("--input", required=True, help="Text file containing URLs to scan (one per line)")
    args = parser.parse_args()

    urls = [l.strip() for l in Path(args.input).read_text().splitlines() if l.strip()]
    existing = load_boards()
    print(f"Loaded {len(existing)} existing boards")

    new_boards = asyncio.run(crawl(urls))
    added = new_boards - existing
    print(f"Discovered {len(added)} new boards")

    if added:
        save_boards(existing | added)
        print("ashby_boards.json updated.")
    else:
        print("No new boards found.")

if __name__ == "__main__":
    main() 