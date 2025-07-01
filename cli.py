"""Command-line interface for jd_filter."""

from __future__ import annotations

import asyncio
from typing import List, Optional, Annotated

import typer

from jd_filter.pipeline import run as run_pipeline

app = typer.Typer(add_completion=False, help="Scrape & filter job boards with hard filters.")


def _split(ctx: typer.Context, param: typer.CallbackParam, value: Optional[str]):  # type: ignore
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@app.command()
def run(
    lever: Annotated[str | None, typer.Option("--lever", callback=_split, help="Comma-separated Lever org slugs.")] = None,  # type: ignore
    greenhouse: Annotated[str | None, typer.Option("--greenhouse", callback=_split)] = None,  # type: ignore
    ashby: Annotated[str | None, typer.Option("--ashby", callback=_split)] = None,  # type: ignore
    since_hrs: int = typer.Option(24, help="Look-back window in hours."),
    csv_path: str = typer.Option("latest_jobs.csv", help="Where to write CSV output."),
    db_uri: str | None = typer.Option(None, help="SQLAlchemy DB URI (e.g. postgresql+psycopg2://user:pass@host/db)."),
):
    """Run the full pipeline from CLI."""

    orgs = {
        "lever": lever or [],
        "greenhouse": greenhouse or [],
        "ashby": ashby or [],
    }
    if not any(orgs.values()):
        typer.echo("No orgs supplied – nothing to do.")
        raise typer.Exit(1)

    asyncio.run(run_pipeline(orgs, since_hrs=since_hrs, csv_path=csv_path, db_uri=db_uri))


if __name__ == "__main__":
    app() 