"""
Internal implementation of news routes.
Not to be imported by other modules — go through modules.news instead.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.news.internal.constants import TICKER_COMPANY_NAME
from modules.news.internal.rss_client import NewsFetchError
from modules.news.internal.schemas import NewsResponse, NewsUniverseResponse, NewsUniverseResult
from modules.news.internal.service import get_news_cached
from shared.db.connection import get_database

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/health")
async def news_health():
    return {"module": "news", "status": "ok", "universe_size": len(TICKER_COMPANY_NAME)}


@router.get("/{ticker}", response_model=NewsResponse)
async def get_news(ticker: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Last 30 days of cached headlines for a ticker. Cache-first, 24h staleness window."""
    ticker = ticker.upper()
    if ticker not in TICKER_COMPANY_NAME:
        raise HTTPException(status_code=400, detail=f"'{ticker}' is not in the supported universe")

    try:
        return await get_news_cached(db, ticker)
    except NewsFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/universe/fetch", response_model=NewsUniverseResponse)
async def fetch_news_universe(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Backfills headlines for all 8 tickers via the cache-aware path."""
    results: list[NewsUniverseResult] = []
    for ticker in TICKER_COMPANY_NAME:
        try:
            response = await get_news_cached(db, ticker)
            results.append(NewsUniverseResult(ticker=ticker, status="ok", count=response.count))
        except NewsFetchError as exc:
            results.append(NewsUniverseResult(ticker=ticker, status="failed", count=0, error=str(exc)))
        # Google News has no published quota like NewsAPI's 100/day, but
        # spacing requests avoids looking like scraping traffic to it.
        await asyncio.sleep(1.0)

    succeeded = sum(1 for r in results if r.status == "ok")
    return NewsUniverseResponse(results=results, succeeded=succeeded, failed=len(results) - succeeded)