"""USA location filter for JobPost objects."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional

from uszipcode import SearchEngine

from ..models import JobPost

# Precompile common patterns
_US_WORDS = re.compile(r"\b(United States|USA|U\.S\.|US)\b", re.I)
_REMOTE_US = re.compile(r"remote[^\n,;]*\b(us|united states)\b", re.I)

# Create a single shared zipcode searcher (lazy)
@lru_cache(maxsize=1)
def _zip_searcher():
    return SearchEngine(simple_zipcode=True)


def _structured_check(loc: Optional[str]) -> bool:
    if not loc:
        return False
    return bool(_US_WORDS.search(loc) or _REMOTE_US.search(loc))


def _zip_code_check(loc: Optional[str]) -> bool:
    if not loc:
        return False
    # Heuristic: extract 5-digit zip
    m = re.search(r"\b(\d{5})\b", loc)
    if not m:
        return False
    zipc = m.group(1)
    res = _zip_searcher().by_zipcode(zipc)
    return bool(res and res.to_dict().get("state"))


def is_us(job: JobPost) -> bool:  # noqa: D401
    """Return True if the job appears to be US-based or Remote (US)."""
    # 1. Structured location field
    if _structured_check(job.location):
        return True

    # 2. Zip code pattern in location
    if _zip_code_check(job.location):
        return True

    # 3. Scan description if available
    if job.description and _US_WORDS.search(job.description):
        return True

    return False 