"""
Orchestration layer between router.py and rss_client/cache_repository.
Same cache-first-then-live policy shape as market_data/internal/service.py.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.news.internal import cache_repository
from modules.news.internal.rss_client import fetch_headlines
from modules.news.internal.schemas import NewsResponse

logger = logging.getLogger("quantai.news.service")


async def get_news_cached(db: AsyncIOMotorDatabase, ticker: str) -> NewsResponse:
    stale = await cache_repository.is_stale(db, ticker)

    if not stale:
        cached_items = await cache_repository.get_cached_items(db, ticker)
        if cached_items:
            logger.info("News cache hit for %s (%d items)", ticker, len(cached_items))
            return NewsResponse(
                ticker=ticker, source="cache", count=len(cached_items), items=cached_items
            )

    logger.info("News cache miss/stale for %s — fetching live", ticker)
    live_items = await fetch_headlines(ticker)
    await cache_repository.upsert_items(db, ticker, live_items)
    await cache_repository.prune_old(db, ticker)

    # Re-read from cache post-upsert so the response reflects the same
    # 30-day-filtered, deduplicated view a cache-hit would return —
    # rather than returning the raw (possibly >30-day, unfiltered) live list.
    fresh_items = await cache_repository.get_cached_items(db, ticker)
    return NewsResponse(ticker=ticker, source="live", count=len(fresh_items), items=fresh_items)