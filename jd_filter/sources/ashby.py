"""Async connector for Ashby job board API."""

from __future__ import annotations

import datetime as _dt
from typing import List

import httpx

from ..models import JobPost

BASE_URL = "https://api.ashbyhq.com/posting-api/organizations/{org}/jobs"

async def fetch_ashby(org: str, *, since_hrs: int = 24) -> List[JobPost]:
    """Return all open postings for *org* created in the last *since_hrs* hours."""
    cutoff = _dt.datetime.utcnow() - _dt.timedelta(hours=since_hrs)
    created_after_iso = cutoff.isoformat(timespec="seconds") + "Z"

    params = {
        "status": "open",
        "created_after": created_after_iso,
    }

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        resp = await client.get(BASE_URL.format(org=org), params=params)
        resp.raise_for_status()
        data: list[dict] = resp.json()

    jobs: list[JobPost] = []
    for p in data:
        jobs.append(
            JobPost(
                id=p.get("id"),
                title=p.get("title", ""),
                company=org,
                location=p.get("location"),
                url=p.get("url"),
                description=p.get("description"),
                created_at=_dt.datetime.fromisoformat(p.get("created_at").rstrip("Z")) if p.get("created_at") else None,
                source="ashby",
            )
        )
    return jobs 