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


class FundamentalsData(BaseModel):
    """
    All fields nullable — yfinance's .info dict is inconsistent across
    tickers (especially NIFTYBEES.NS, an ETF, which lacks P/E/earnings
    growth entirely). Missing data must surface as null, never be
    silently defaulted to 0, which would be a fabricated number.
    """
    pe_ratio: float | None = None
    forward_pe: float | None = None
    earnings_growth: float | None = None
    market_cap: int | None = None
    sector: str | None = None


class FundamentalsResponse(BaseModel):
    ticker: str
    source: Literal["live", "cache"]
    data: FundamentalsData


class FundamentalsUniverseResult(BaseModel):
    ticker: str
    status: Literal["ok", "failed"]
    error: str | None = None


class FundamentalsUniverseResponse(BaseModel):
    results: list[FundamentalsUniverseResult]
    succeeded: int
    failed: int