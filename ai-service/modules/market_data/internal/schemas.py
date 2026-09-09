"""
Pydantic response models for market_data endpoints.
Kept separate from router.py so schemas are reusable/importable
without pulling in FastAPI route decorators.
"""
from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel


class OHLCVBar(BaseModel):
    date: date_type
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


class OHLCVResponse(BaseModel):
    ticker: str
    source: Literal["live", "cache"]
    bar_count: int
    bars: list[OHLCVBar]


class UniverseFetchResult(BaseModel):
    ticker: str
    status: Literal["ok", "failed"]
    bar_count: int
    error: str | None = None


class UniverseFetchResponse(BaseModel):
    results: list[UniverseFetchResult]
    succeeded: int
    failed: int