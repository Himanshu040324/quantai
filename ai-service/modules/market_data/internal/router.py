"""
Internal implementation of market_data routes.
Not to be imported by other modules — go through modules.market_data instead.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.market_data.internal.constants import TICKER_UNIVERSE
from modules.market_data.internal.schemas import (
    FundamentalsResponse,
    FundamentalsUniverseResponse,
    FundamentalsUniverseResult,
    OHLCVResponse,
    UniverseFetchResponse,
    UniverseFetchResult,
)
from modules.market_data.internal.service import get_fundamentals_cached, get_ohlcv_cached
from modules.market_data.internal.yfinance_client import TickerFetchError
from shared.db.connection import get_database

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/health")
async def market_data_health():
    return {"module": "market_data", "status": "ok", "universe_size": len(TICKER_UNIVERSE)}


@router.get("/ohlcv/{ticker}", response_model=OHLCVResponse)
async def get_ohlcv(
    ticker: str, years: int = 5, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years must be between 1 and 10")

    ticker = ticker.upper()
    try:
        return await get_ohlcv_cached(db, ticker, years)
    except TickerFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ohlcv/universe/fetch", response_model=UniverseFetchResponse)
async def fetch_universe(
    years: int = 5, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years must be between 1 and 10")

    results: list[UniverseFetchResult] = []
    for ticker in TICKER_UNIVERSE:
        try:
            response = await get_ohlcv_cached(db, ticker, years)
            results.append(
                UniverseFetchResult(ticker=ticker, status="ok", bar_count=response.bar_count)
            )
        except TickerFetchError as exc:
            results.append(
                UniverseFetchResult(ticker=ticker, status="failed", bar_count=0, error=str(exc))
            )
        await asyncio.sleep(0.3)

    succeeded = sum(1 for r in results if r.status == "ok")
    return UniverseFetchResponse(results=results, succeeded=succeeded, failed=len(results) - succeeded)


@router.get("/fundamentals/{ticker}", response_model=FundamentalsResponse)
async def get_fundamentals(ticker: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Fetch fundamentals (P/E, forward P/E, earnings growth, market cap,
    sector) for a single ticker. Cache-first, 7-day staleness window.
    """
    ticker = ticker.upper()
    try:
        return await get_fundamentals_cached(db, ticker)
    except TickerFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/fundamentals/universe/fetch", response_model=FundamentalsUniverseResponse)
async def fetch_fundamentals_universe(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Backfills fundamentals for all 8 tickers. Note NIFTYBEES.NS (an ETF)
    is expected to return mostly-null fields, not a failure — ETFs
    genuinely don't have a P/E ratio the way individual stocks do.
    """
    results: list[FundamentalsUniverseResult] = []
    for ticker in TICKER_UNIVERSE:
        try:
            await get_fundamentals_cached(db, ticker)
            results.append(FundamentalsUniverseResult(ticker=ticker, status="ok"))
        except TickerFetchError as exc:
            results.append(
                FundamentalsUniverseResult(ticker=ticker, status="failed", error=str(exc))
            )
        await asyncio.sleep(0.3)

    succeeded = sum(1 for r in results if r.status == "ok")
    return FundamentalsUniverseResponse(
        results=results, succeeded=succeeded, failed=len(results) - succeeded
    )