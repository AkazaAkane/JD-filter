"""Async connector for Lever job board API."""

from __future__ import annotations

import datetime as _dt
from typing import List

import httpx

from ..models import JobPost

BASE_URL = "https://api.lever.co/v0/postings/{org}"

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