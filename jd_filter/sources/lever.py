"""Async connector for Lever job board API."""

from __future__ import annotations

import datetime as _dt
from typing import List
import json
from pathlib import Path
from httpx import HTTPStatusError

import httpx

from ..models import JobPost

BASE_URL = "https://api.lever.co/v0/postings/{org}"

# Path to slug cache (stored alongside this module)
_CACHE_FILE: Path = Path(__file__).with_name("lever_slugs.json")


def _load_cache() -> dict[str, int]:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text())  # type: ignore
        except Exception:
            pass
    return {}


def _save_cache(cache: dict[str, int]) -> None:
    _CACHE_FILE.write_text(json.dumps(cache, indent=2))


async def validate_lever_slugs(slugs: list[str]) -> list[str]:
    """Return *slugs* that are valid (no repeated 404/410). Persistent cache controls dropping.

    When a slug triggers a 404/410, its fail counter increments; after 3 consecutive
    failures it is removed from the returned list and persisted.
    """
    cache = _load_cache()
    valid: list[str] = []

    async with httpx.AsyncClient(timeout=10) as client:
        for slug in slugs:
            try:
                resp = await client.get(
                    BASE_URL.format(org=slug), params={"limit": 1, "mode": "json"}
                )
                resp.raise_for_status()
                # Success -> reset failures
                cache.pop(slug, None)
                valid.append(slug)
            except HTTPStatusError as exc:
                if exc.response.status_code in (404, 410):
                    cache[slug] = cache.get(slug, 0) + 1
                    if cache[slug] < 3:
                        # keep trying until we hit the threshold
                        valid.append(slug)
                else:
                    valid.append(slug)  # keep slug for transient errors

    # Drop slugs that have reached threshold
    dropped = [s for s, fails in cache.items() if fails >= 3]
    for d in dropped:
        cache.pop(d, None)

    _save_cache(cache)

    # Emit simple metric via stdout
    try:
        import logging

        logging.getLogger(__name__).info(
            "collector_status.lever %s/%s", len(valid), len(slugs)
        )
    except Exception:
        pass

    # Filter out dropped slugs
    return [s for s in valid if s not in dropped]


async def fetch_lever(org: str, *, since_hrs: int = 24) -> List[JobPost]:
    """Return all postings for *org* created in the last *since_hrs* hours.

    Lever API accepts a `createdAt` query parameter in milliseconds epoch.
    """
    cutoff = _dt.datetime.utcnow() - _dt.timedelta(hours=since_hrs)
    created_ms = int(cutoff.timestamp() * 1000)

    params = {
        "mode": "json",
        "createdAt": created_ms,
    }

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        resp = await client.get(BASE_URL.format(org=org), params=params)
        resp.raise_for_status()
        data: list[dict] = resp.json()

    jobs: list[JobPost] = []
    for p in data:
        jobs.append(
            JobPost(
                id=p["id"],
                title=p.get("text", ""),
                company=org,
                location=p.get("categories", {}).get("location"),
                url=p["hostedUrl"],
                description=p.get("description"),
                created_at=_dt.datetime.utcfromtimestamp(p.get("createdAt", 0) / 1000),
                source="lever",
            )
        )
    return jobs 