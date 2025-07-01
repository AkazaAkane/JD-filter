"""Async connector for Ashby job board API."""

from __future__ import annotations

import datetime as _dt
from typing import List
import json
from pathlib import Path
from httpx import HTTPStatusError

import httpx

from ..models import JobPost

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board}"

# Path to persistent board registry
_BOARDS_FILE: Path = Path(__file__).with_name("ashby_boards.json")


def _load_registry() -> dict[str, int]:
    if _BOARDS_FILE.exists():
        try:
            return json.loads(_BOARDS_FILE.read_text())  # type: ignore
        except Exception:
            pass
    return {}


def _save_registry(reg: dict[str, int]) -> None:
    _BOARDS_FILE.write_text(json.dumps(reg, indent=2))


async def validate_ashby_boards(boards: list[str]) -> list[str]:
    """Return boards that respond 200; increment fail counters on 404/410.

    After 3 consecutive failures a board is skipped until rediscovered.
    """
    reg = _load_registry()
    valid: list[str] = []

    async with httpx.AsyncClient(timeout=10) as client:
        for board in boards:
            try:
                resp = await client.get(
                    BASE_URL.format(board=board),
                    params={"limit": 1},
                )
                resp.raise_for_status()
                reg.pop(board, None)
                valid.append(board)
            except HTTPStatusError as exc:
                if exc.response.status_code in (404, 410):
                    reg[board] = reg.get(board, 0) + 1
                    if reg[board] < 3:
                        valid.append(board)
                else:
                    valid.append(board)

    dropped = [b for b, fails in reg.items() if fails >= 3]
    for b in dropped:
        reg.pop(b, None)

    _save_registry(reg)

    # metric
    try:
        import logging

        logging.getLogger(__name__).info(
            "collector_status.ashby %s/%s", len(valid), len(boards)
        )
    except Exception:
        pass

    return [b for b in valid if b not in dropped]


async def fetch_ashby(board: str, *, since_hrs: int = 24) -> List[JobPost]:
    """Return postings from *board* created in the last *since_hrs* hours using the public feed."""
    cutoff = _dt.datetime.utcnow() - _dt.timedelta(hours=since_hrs)
    created_after_iso = cutoff.isoformat(timespec="seconds") + "Z"

    params = {
        "includeCompensation": "true",
        "created_after": created_after_iso,
    }

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        resp = await client.get(BASE_URL.format(board=board), params=params)
        resp.raise_for_status()
        data: list[dict] = resp.json()

    jobs: list[JobPost] = []
    for p in data:
        posted = p.get("createdAt") or p.get("created_at")
        jobs.append(
            JobPost(
                id=str(p.get("id")),
                title=p.get("title", ""),
                company=p.get("companyName") or board,
                location=p.get("jobLocation", {}).get("location") if isinstance(p.get("jobLocation"), dict) else p.get("location"),
                url=p.get("url"),
                description=p.get("descriptionPlain") or p.get("description"),
                created_at=_dt.datetime.fromisoformat(posted.rstrip("Z")) if posted else None,
                source="ashby",
            )
        )
    return jobs 