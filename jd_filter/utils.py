"""Utility helpers shared across jd_filter modules."""

from __future__ import annotations

import hashlib
import os
from typing import Iterable, List, Sequence, TypeVar

from .models import JobPost

T = TypeVar("T")


def dedupe(jobs: Sequence[JobPost]) -> List[JobPost]:
    """Return *jobs* stripped of duplicates based on URL hash."""
    seen: set[str] = set()
    unique: list[JobPost] = []
    for j in jobs:
        sig = hashlib.sha1(str(j.url).encode()).hexdigest()
        if sig not in seen:
            seen.add(sig)
            unique.append(j)
    return unique


def chunk(seq: Sequence[T], size: int) -> Iterable[Sequence[T]]:  # pragma: no cover
    """Yield *size*-sized chunks from *seq*."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def get_env(key: str, default: str | None = None) -> str:
    """Return env var *key* or *default*, raising if missing & no default supplied."""
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f"Environment variable '{key}' must be set")
    return val 