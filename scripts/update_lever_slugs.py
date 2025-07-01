#!/usr/bin/env python
"""Refresh lever_slugs.json using SerpAPI or GitHub code search.

Requires env var SERPAPI_KEY. Falls back to public GitHub search if no key.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Set

import httpx
from tqdm.asyncio import tqdm

SLUGS_FILE = Path(__file__).resolve().parent.parent / "jd_filter" / "sources" / "lever_slugs.json"
PATTERN = re.compile(r"jobs\.lever\.co/([A-Za-z0-9\-]+)")
SERP_ENDPOINT = "https://serpapi.com/search.json"


def load_slugs() -> Set[str]:
    if SLUGS_FILE.exists():
        try:
            return set(json.loads(SLUGS_FILE.read_text()).keys())
        except Exception:
            pass
    return set()


def save_slugs(slugs: Set[str]) -> None:
    data = {s: {"fails": 0} for s in sorted(slugs)}
    SLUGS_FILE.write_text(json.dumps(data, indent=2))


async def search_serpapi(query: str, pages: int = 3) -> Set[str]:
    key = os.getenv("SERPAPI_KEY")
    if not key:
        print("SERPAPI_KEY not set – skipping SerpAPI search", file=sys.stderr)
        return set()
    params_base = {
        "engine": "google",
        "q": query,
        "num": 100,
        "api_key": key,
    }
    found: Set[str] = set()
    async with httpx.AsyncClient() as client:
        for page in range(pages):
            params = params_base | {"start": page * 100}
            r = await client.get(SERP_ENDPOINT, params=params, timeout=20)
            r.raise_for_status()
            for result in r.json().get("organic_results", []):
                url = result.get("link", "")
                m = PATTERN.search(url)
                if m:
                    found.add(m.group(1))
    return found


async def main() -> None:  # pragma: no cover
    print("Refreshing Lever slugs…")
    existing = load_slugs()
    print(f"Loaded {len(existing)} existing slugs")

    serp_slugs = await search_serpapi("site:jobs.lever.co", pages=3)
    print(f"SerpAPI found {len(serp_slugs)} slugs")

    updated = existing | serp_slugs
    save_slugs(updated)
    print(f"lever_slugs.json now holds {len(updated)} slugs")

if __name__ == "__main__":
    asyncio.run(main()) 