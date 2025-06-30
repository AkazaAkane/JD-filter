"""Async connector for Greenhouse API."""

from __future__ import annotations

import datetime as _dt
from typing import List

import httpx

from ..models import JobPost

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{org}/jobs"

async def fetch_greenhouse(org: str, *, since_hrs: int = 24) -> List[JobPost]:
    """Return all postings for *org* created in the last *since_hrs* hours."""
    cutoff = _dt.datetime.utcnow() - _dt.timedelta(hours=since_hrs)
    created_after = cutoff.strftime("%Y-%m-%d")

    params = {
        "created_after": created_after,
    }

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        resp = await client.get(BASE_URL.format(org=org), params=params)
        resp.raise_for_status()
        data = resp.json()

    # the API wraps results under "jobs"
    postings: list[dict] = data.get("jobs", []) if isinstance(data, dict) else data  # fallback

    jobs: list[JobPost] = []
    for p in postings:
        jobs.append(
            JobPost(
                id=str(p.get("id")),
                title=p.get("title", ""),
                company=org,
                location=(p.get("location", {}) or {}).get("name") if isinstance(p.get("location"), dict) else p.get("location"),
                url=p.get("absolute_url"),
                description=p.get("content"),
                created_at=_dt.datetime.strptime(p.get("created_at"), "%Y-%m-%dT%H:%M:%S%z").astimezone(_dt.timezone.utc).replace(tzinfo=None) if p.get("created_at") else None,
                source="greenhouse",
            )
        )
    return jobs 