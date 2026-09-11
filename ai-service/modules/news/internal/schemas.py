from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    link: str
    published_at: datetime
    source: str | None = None


class NewsResponse(BaseModel):
    ticker: str
    source: Literal["live", "cache"]
    count: int
    items: list[NewsItem]


class NewsUniverseResult(BaseModel):
    ticker: str
    status: Literal["ok", "failed"]
    count: int
    error: str | None = None


class NewsUniverseResponse(BaseModel):
    results: list[NewsUniverseResult]
    succeeded: int
    failed: int