"""
Orchestration layer between router.py and the yfinance/cache internals.
This is where "check cache, refetch if stale" policy lives for both
OHLCV and fundamentals — router.py stays a thin HTTP layer.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.market_data.internal import cache_repository, fundamentals_repository
from modules.market_data.internal.schemas import FundamentalsResponse, OHLCVResponse
from modules.market_data.internal.yfinance_client import fetch_fundamentals, fetch_ohlcv

logger = logging.getLogger("quantai.market_data.service")


async def get_ohlcv_cached(db: AsyncIOMotorDatabase, ticker: str, years: int) -> OHLCVResponse:
    stale = await cache_repository.is_stale(db, ticker)

    if not stale:
        cached_bars = await cache_repository.get_cached_bars(db, ticker, years)
        if cached_bars:
            logger.info("OHLCV cache hit for %s (%d bars)", ticker, len(cached_bars))
            return OHLCVResponse(
                ticker=ticker, source="cache", bar_count=len(cached_bars), bars=cached_bars
            )

    logger.info("OHLCV cache miss/stale for %s — fetching live", ticker)
    live_bars = await fetch_ohlcv(ticker, years=years)
    await cache_repository.upsert_bars(db, ticker, live_bars)

    return OHLCVResponse(ticker=ticker, source="live", bar_count=len(live_bars), bars=live_bars)


async def get_fundamentals_cached(db: AsyncIOMotorDatabase, ticker: str) -> FundamentalsResponse:
    """
    Cache-first read with a 7-day window. Same pattern as OHLCV but
    against fundamentals_repository instead of cache_repository.
    """
    cached = await fundamentals_repository.get_cached(db, ticker)

    if cached is not None:
        data, fetched_at = cached
        if not fundamentals_repository.is_stale(fetched_at):
            logger.info("Fundamentals cache hit for %s", ticker)
            return FundamentalsResponse(ticker=ticker, source="cache", data=data)

    logger.info("Fundamentals cache miss/stale for %s — fetching live", ticker)
    live_data = await fetch_fundamentals(ticker)
    await fundamentals_repository.upsert(db, ticker, live_data)

    return FundamentalsResponse(ticker=ticker, source="live", data=live_data)