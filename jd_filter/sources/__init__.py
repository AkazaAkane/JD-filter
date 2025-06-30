"""Source connectors that retrieve job postings from various ATS/job boards.

Each module exposes an async `fetch_<source>() -> list[jd_filter.models.JobPost]`.
"""

from importlib import import_module
from types import ModuleType
from typing import Any, Callable, List

from ..models import JobPost

__all__: list[str] = [
    "fetch_lever",
    "fetch_greenhouse",
    "fetch_ashby",
]

# Lazy import wrappers so the heavy dependencies are loaded only when used.

def _lazy(name: str, func_name: str) -> Callable[..., Any]:
    def _wrapper(*args: Any, **kwargs: Any):
        mod: ModuleType = import_module(f"jd_filter.sources.{name}")
        return getattr(mod, func_name)(*args, **kwargs)

    _wrapper.__name__ = func_name
    return _wrapper

fetch_lever: Callable[..., Any] = _lazy("lever", "fetch_lever")  # type: ignore
fetch_greenhouse: Callable[..., Any] = _lazy("greenhouse", "fetch_greenhouse")  # type: ignore
fetch_ashby: Callable[..., Any] = _lazy("ashby", "fetch_ashby")  # type: ignore 