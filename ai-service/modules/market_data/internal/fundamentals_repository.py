"""
Mongo persistence for fundamentals data. Separate collection and
separate staleness policy from price_cache (cache_repository.py) —
fundamentals update far less often than daily prices, so mixing them
into one collection/policy would either over-fetch prices or
under-refresh fundamentals.

Document shape (ONE document per ticker, not per date — fundamentals
are a current-snapshot, not a time series):
{
    ticker: str,
    pe_ratio, forward_pe, earnings_growth: float | None,
    market_cap: int | None,
    sector: str | None,
    fetched_at: datetime (UTC)
}
"""
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

from modules.market_data.internal.constants import FUNDAMENTALS_STALENESS_HOURS
from modules.market_data.internal.schemas import FundamentalsData

COLLECTION_NAME = "fundamentals_cache"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Call once on startup. Idempotent."""
    await db[COLLECTION_NAME].create_index([("ticker", ASCENDING)], unique=True)


async def get_cached(db: AsyncIOMotorDatabase, ticker: str) -> tuple[FundamentalsData, datetime] | None:
    """Returns (data, fetched_at) if a document exists, else None."""
    doc = await db[COLLECTION_NAME].find_one({"ticker": ticker})
    if doc is None:
        return None
    data = FundamentalsData(
        pe_ratio=doc.get("pe_ratio"),
        forward_pe=doc.get("forward_pe"),
        earnings_growth=doc.get("earnings_growth"),
        market_cap=doc.get("market_cap"),
        sector=doc.get("sector"),
    )
    return data, doc["fetched_at"]


def is_stale(fetched_at: datetime, max_age_hours: int = FUNDAMENTALS_STALENESS_HOURS) -> bool:
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - fetched_at > timedelta(hours=max_age_hours)


async def upsert(db: AsyncIOMotorDatabase, ticker: str, data: FundamentalsData) -> None:
    now = datetime.now(timezone.utc)
    await db[COLLECTION_NAME].update_one(
        {"ticker": ticker},
        {
            "$set": {
                "ticker": ticker,
                "pe_ratio": data.pe_ratio,
                "forward_pe": data.forward_pe,
                "earnings_growth": data.earnings_growth,
                "market_cap": data.market_cap,
                "sector": data.sector,
                "fetched_at": now,
            }
        },
        upsert=True,
    )