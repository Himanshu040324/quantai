"""
Mongo persistence for news headlines. Separate collection and policy
from price_cache/fundamentals_cache — one document per headline,
unique on (ticker, link) so re-fetching the same feed never duplicates
a headline, and old headlines age out via a 30-day retention query
(not a hard delete on every fetch — see prune_old for that).
"""
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, UpdateOne

from modules.news.internal.constants import NEWS_STALENESS_HOURS, RETENTION_DAYS
from modules.news.internal.schemas import NewsItem

COLLECTION_NAME = "news_cache"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION_NAME].create_index(
        [("ticker", ASCENDING), ("link", ASCENDING)], unique=True
    )
    # Supports get_cached_items' range query and prune_old's cleanup query.
    await db[COLLECTION_NAME].create_index([("ticker", ASCENDING), ("published_at", ASCENDING)])


async def get_latest_fetch_time(db: AsyncIOMotorDatabase, ticker: str) -> datetime | None:
    doc = await db[COLLECTION_NAME].find_one(
        {"ticker": ticker}, sort=[("fetched_at", -1)], projection={"fetched_at": 1}
    )
    return doc["fetched_at"] if doc else None


async def is_stale(
    db: AsyncIOMotorDatabase, ticker: str, max_age_hours: int = NEWS_STALENESS_HOURS
) -> bool:
    latest = await get_latest_fetch_time(db, ticker)
    if latest is None:
        return True
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - latest > timedelta(hours=max_age_hours)


async def upsert_items(db: AsyncIOMotorDatabase, ticker: str, items: list[NewsItem]) -> int:
    if not items:
        return 0

    now = datetime.now(timezone.utc)
    operations = [
        UpdateOne(
            {"ticker": ticker, "link": item.link},
            {
                "$set": {
                    "ticker": ticker,
                    "title": item.title,
                    "link": item.link,
                    "published_at": item.published_at,
                    "source": item.source,
                    "fetched_at": now,
                }
            },
            upsert=True,
        )
        for item in items
    ]
    result = await db[COLLECTION_NAME].bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count


async def get_cached_items(
    db: AsyncIOMotorDatabase, ticker: str, retention_days: int = RETENTION_DAYS
) -> list[NewsItem]:
    """Only returns headlines published within the retention window, newest first."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cursor = (
        db[COLLECTION_NAME]
        .find({"ticker": ticker, "published_at": {"$gte": cutoff}})
        .sort("published_at", -1)
    )
    docs = await cursor.to_list(length=None)
    return [
        NewsItem(
            title=doc["title"],
            link=doc["link"],
            published_at=doc["published_at"],
            source=doc.get("source"),
        )
        for doc in docs
    ]


async def prune_old(db: AsyncIOMotorDatabase, ticker: str, retention_days: int = RETENTION_DAYS) -> int:
    """
    Hard-deletes headlines older than the retention window. Called
    after a live refetch, not on cache-hit reads — keeps the collection
    from growing unbounded across months of daily fetches.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await db[COLLECTION_NAME].delete_many(
        {"ticker": ticker, "published_at": {"$lt": cutoff}}
    )
    return result.deleted_count