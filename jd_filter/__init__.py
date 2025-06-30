"""Top-level package for JD-Filter.

Exposes the main data model (`JobPost`) and convenience `run_pipeline()` helper so
library consumers can do:

    from jd_filter import run_pipeline
"""

from importlib import metadata as _metadata

from .models import JobPost  # noqa: F401 re-export
from .pipeline import run as run_pipeline  # noqa: F401

__all__: list[str] = [
    "JobPost",
    "run_pipeline",
]

try:
    __version__ = _metadata.version("jd-filter")
except _metadata.PackageNotFoundError:  # pragma: no cover – local dev
    __version__ = "0.0.0" 