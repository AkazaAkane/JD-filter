"""End-to-end orchestrator for scraping & hard-filtering job postings.

Typical usage (sync wrapper):

    import asyncio
    from jd_filter.pipeline import run

    asyncio.run(run({
        "lever": ["openai", "duolingo"],
        "greenhouse": ["deepmind"],
        "ashby": ["scaleai"],
    }, db_uri="postgresql+psycopg2://user:pass@localhost/jdjobs"))
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import sqlalchemy as sa

from .filters import is_us, passes_keyword_filter
from .models import JobPost
from .sources import fetch_ashby, fetch_greenhouse, fetch_lever
from .sources.lever import validate_lever_slugs
from .sources.ashby import validate_ashby_boards
from .utils import dedupe

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def _flatten_jobs(jobs: List[JobPost]) -> pd.DataFrame:
    return pd.DataFrame([j.model_dump() for j in jobs])


async def _gather_jobs(orgs: Dict[str, List[str]], since_hrs: int) -> List[JobPost]:
    tasks: List[asyncio.Task] = []

    lever_slugs = await validate_lever_slugs(orgs.get("lever") or [])
    for org in lever_slugs:
        tasks.append(asyncio.create_task(fetch_lever(org, since_hrs=since_hrs)))
    for org in orgs.get("greenhouse", []):
        tasks.append(asyncio.create_task(fetch_greenhouse(org, since_hrs=since_hrs)))
    ashby_boards = await validate_ashby_boards(orgs.get("ashby") or [])
    for board in ashby_boards:
        tasks.append(asyncio.create_task(fetch_ashby(board, since_hrs=since_hrs)))

    results: List[JobPost] = []
    for t in asyncio.as_completed(tasks):
        try:
            res = await t
            results.extend(res)
        except Exception as exc:  # pragma: no cover – network failures
            logger.warning("Fetch failed: %s", exc)
    return results


async def run(
    orgs: Dict[str, List[str]],
    *,
    since_hrs: int = 24,
    csv_path: str | Path | None = "latest_jobs.csv",
    db_uri: str | None = None,
):
    """Fetch, hard-filter and persist job postings.

    Parameters
    ----------
    orgs
        Mapping like ``{"lever": ["openai", "duolingo"]}``.
    since_hrs
        Look-back window for *new* postings.
    csv_path
        If provided, write filtered jobs to this CSV path.
    db_uri
        If provided, insert rows into Postgres via SQLAlchemy.
    """

    raw_jobs = await _gather_jobs(orgs, since_hrs)
    logger.info("Fetched %d raw jobs", len(raw_jobs))

    unique_jobs = dedupe(raw_jobs)
    logger.info("After dedupe: %d", len(unique_jobs))

    filtered: List[JobPost] = [j for j in unique_jobs if is_us(j) and passes_keyword_filter(j)]
    logger.info("After hard filters: %d", len(filtered))

    if not filtered:
        logger.warning("No jobs after filtering – nothing to persist.")
        return []

    df = _flatten_jobs(filtered)

    # CSV output
    if csv_path:
        df.to_csv(csv_path, index=False)
        logger.info("Wrote %s", csv_path)

    # Postgres output
    if db_uri:
        engine = sa.create_engine(db_uri)
        with engine.begin() as conn:
            df.to_sql("jobs", conn, if_exists="append", index=False, method="multi")
        logger.info("Inserted %d rows into Postgres", len(df))

    return filtered 