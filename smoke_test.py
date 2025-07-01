"""Lightweight smoke test for the hard-filter pipeline.

Usage (inside virtualenv):

    python smoke_test.py

It patches the source connectors to return synthetic job postings so the test
runs offline and deterministically.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from jd_filter.models import JobPost
from jd_filter import pipeline
import jd_filter.sources as sources

# ---------------------------------------------------------------------------
# Build mock job postings ----------------------------------------------------
# ---------------------------------------------------------------------------

good_us_job = JobPost(
    id="1",
    title="Machine Learning Engineer",
    company="AcmeAI",
    location="San Francisco, CA, United States",
    url="https://jobs.example.com/1",
    description="Work with PyTorch on LLMs.",
    source="lever",
)

bad_keyword_job = JobPost(
    id="2",
    title="Senior Sales Executive",
    company="SalesCorp",
    location="New York, NY, US",
    url="https://jobs.example.com/2",
    description="Close enterprise deals.",
    source="lever",
)

non_us_job = JobPost(
    id="3",
    title="ML Engineer",
    company="EuroAI",
    location="Berlin, Germany",
    url="https://jobs.example.com/3",
    description="AI and Deep Learning using PyTorch.",
    source="lever",
)

MOCK_JOBS = [good_us_job, bad_keyword_job, non_us_job]


# ---------------------------------------------------------------------------
# Monkey-patch async fetchers -------------------------------------------------
# ---------------------------------------------------------------------------

async def _mock_fetch(org: str, since_hrs: int = 24):  # noqa: D401
    # Return the same MOCK_JOBS regardless of org
    return MOCK_JOBS

# Apply the patch
sources.fetch_lever = _mock_fetch  # type: ignore
sources.fetch_greenhouse = _mock_fetch  # type: ignore
sources.fetch_ashby = _mock_fetch  # type: ignore


# ---------------------------------------------------------------------------
# Run pipeline ---------------------------------------------------------------
# ---------------------------------------------------------------------------

def main():  # noqa: D401
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "out.csv"
        asyncio.run(
            pipeline.run(
                {
                    "lever": ["dummy"],
                    "greenhouse": [],
                    "ashby": [],
                },
                csv_path=csv_path,
                db_uri=None,
            )
        )
        assert csv_path.exists(), "CSV output not created!"
        rows = csv_path.read_text().strip().splitlines()
        assert len(rows) == 2, f"Expected header + 1 job, got {len(rows)} lines"  # header + good_us_job
        print("Smoke test passed. Filter kept 1 job as expected.")


if __name__ == "__main__":
    main() 