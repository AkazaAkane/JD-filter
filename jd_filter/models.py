"""Canonical data models used across jd_filter."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class JobPost(BaseModel):
    """Normalized representation of a single job posting."""

    id: str = Field(..., description="Unique identifier from the upstream source")
    title: str
    company: str
    location: Optional[str] = None
    url: HttpUrl
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    source: str = Field(..., description="lever | greenhouse | ashby | serpapi | …")

    model_config = {"extra": "ignore"} 