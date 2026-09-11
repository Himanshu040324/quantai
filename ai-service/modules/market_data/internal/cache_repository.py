"""
Mongo persistence for OHLCV data. This is the ONLY file that touches
the price_cache collection directly — router.py goes through the
functions here, never db["price_cache"] itself. Keeps the caching
policy (schema, staleness rule) centralized and swappable.

Document shape (one document per ticker+date bar):
{
    ticker: str,
    date: str (ISO "YYYY-MM-DD", not a BSON date — avoids timezone
               ambiguity when comparing to yfinance's date-only bars),
    open, high, low, close, adj_close: float,
    volume: int,
    fetched_at: datetime (UTC) — used for staleness checks
}

Unique index on (ticker, date) enforces one bar per ticker per day and
makes upserts idempotent — re-fetching the same range never duplicates rows.
"""
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, UpdateOne

from modules.market_data.internal.schemas import OHLCVBar

COLLECTION_NAME = "price_cache"

DEFAULT_STALENESS_HOURS = 24  # docx Phase 2: "re-fetch if data is >1 day old"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Call once on startup. Idempotent — safe to call every boot."""
    await db[COLLECTION_NAME].create_index(
        [("ticker", ASCENDING), ("date", ASCENDING)], unique=True
    )


async def get_latest_fetch_time(db: AsyncIOMotorDatabase, ticker: str) -> datetime | None:
    """
    Returns the most recent fetched_at for this ticker, or None if we've
    never cached it. Used to decide staleness before hitting yfinance.
    """
    doc = await db[COLLECTION_NAME].find_one(
        {"ticker": ticker}, sort=[("fetched_at", -1)], projection={"fetched_at": 1}
    )
    return doc["fetched_at"] if doc else None


async def is_stale(
    db: AsyncIOMotorDatabase, ticker: str, max_age_hours: int = DEFAULT_STALENESS_HOURS
) -> bool:
    """True if there's no cache yet, or the cache is older than max_age_hours."""
    latest = await get_latest_fetch_time(db, ticker)
    if latest is None:
        return True
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - latest > timedelta(hours=max_age_hours)


async def upsert_bars(db: AsyncIOMotorDatabase, ticker: str, bars: list[OHLCVBar]) -> int:
    """
    Bulk upsert — one operation per bar, keyed on (ticker, date), so
    re-fetching an overlapping date range updates existing rows instead
    of duplicating them. Returns the number of bars written.
    """
    if not bars:
        return 0

    now = datetime.now(timezone.utc)
    operations = [
        UpdateOne(
            {"ticker": ticker, "date": bar.date.isoformat()},
            {
                "$set": {
                    "ticker": ticker,
                    "date": bar.date.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "adj_close": bar.adj_close,
                    "volume": bar.volume,
                    "fetched_at": now,
                }
            },
            upsert=True,
        )
        for bar in bars
    ]
    result = await db[COLLECTION_NAME].bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count


async def get_cached_bars(
    db: AsyncIOMotorDatabase, ticker: str, years: int
) -> list[OHLCVBar]:
    """Reads back cached bars for a ticker, most recent `years` worth, sorted ascending by date."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=years * 365)).date().isoformat()
    cursor = (
        db[COLLECTION_NAME]
        .find({"ticker": ticker, "date": {"$gte": cutoff}})
        .sort("date", ASCENDING)
    )
    docs = await cursor.to_list(length=None)
    return [
        OHLCVBar(
            date=doc["date"],
            open=doc["open"],
            high=doc["high"],
            low=doc["low"],
            close=doc["close"],
            adj_close=doc["adj_close"],
            volume=doc["volume"],
        )
        for doc in docs
    ]