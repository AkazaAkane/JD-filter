"""Fetch real job postings from configured orgs and print matches.

Adjust the ORGS mapping below to include the companies you want to query.
Run:

    python fetch_jobs.py
"""

from __future__ import annotations

import asyncio
from textwrap import shorten

from jd_filter.pipeline import run as run_pipeline

# ---------------------------------------------------------------------------
# Configure org slugs you care about ------------------------------------------------
# For Lever / Greenhouse / Ashby, use the slug appearing in the board URL, e.g.
#   https://jobs.lever.co/openai   -> "openai"
#   https://boards.greenhouse.io/deepmind -> "deepmind"
# ---------------------------------------------------------------------------

ORGS = {
    "lever": ["openai", "duolingo"],
    "greenhouse": ["deepmind"],
    "ashby": ["scaleai"],
}

SINCE_HOURS = 24  # look-back window


async def main():  # noqa: D401
    matches = await run_pipeline(ORGS, since_hrs=SINCE_HOURS, csv_path=None, db_uri=None)
    print(f"\nFound {len(matches)} matching jobs in the last {SINCE_HOURS} hours:\n")
    for j in matches:
        print(f"- {j.company}: {j.title} ({j.location}) -> {j.url}")
        print("  ", shorten(j.description or "", width=120, placeholder="…"))
        print()


if __name__ == "__main__":
    asyncio.run(main()) 