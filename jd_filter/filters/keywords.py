"""Keyword-based hard filter for JobPost objects."""

from __future__ import annotations

from typing import Set

from ..models import JobPost

_BAD_KEYWORDS: Set[str] = {
    "sales",
    "account executive",
    "human resources",
    "hr",
    "recruiter",
    "talent acquisition",
    "customer success",
    "customer support",
    "marketing",
    "legal",
    "product manager",
    "senior",
    "5+ years",
    "6+ years",
    "7+ years",
    "8+ years",
    "9+ years",
    "10+ years",
}

# A posting must contain *at least one* of these good keywords.
_GOOD_KEYWORDS: Set[str] = {
    "pytorch",
    "machine learning",
    "ml engineer",
    "software engineer - ml",
    "llm",
    "ai",
    "deep learning",
}


def passes_keyword_filter(job: JobPost) -> bool:  # noqa: D401
    """Return True if the job does *not* contain obvious bad keywords."""
    blob = f"{job.title or ''} {job.description or ''}".lower()

    # 1. Must include at least one good keyword
    if not any(good in blob for good in _GOOD_KEYWORDS):
        return False

    # 2. Must NOT include any bad keywords
    return not any(bad in blob for bad in _BAD_KEYWORDS) 