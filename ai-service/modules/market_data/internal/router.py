"""
Internal implementation of market_data routes.
Not to be imported by other modules — go through modules.market_data instead.
"""
import asyncio

from fastapi import APIRouter, HTTPException

from modules.market_data.internal.constants import TICKER_UNIVERSE
from modules.market_data.internal.schemas import (
    OHLCVResponse,
    UniverseFetchResponse,
    UniverseFetchResult,
)
from modules.market_data.internal.yfinance_client import TickerFetchError, fetch_ohlcv

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/health")
async def market_data_health():
    return {"module": "market_data", "status": "ok", "universe_size": len(TICKER_UNIVERSE)}


@router.get("/ohlcv/{ticker}", response_model=OHLCVResponse)
async def get_ohlcv(ticker: str, years: int = 5):
    """
    Fetch 1-{years} of daily OHLCV for a single ticker, live from yfinance.
    No caching yet — Step 3 adds the Mongo cache-check in front of this.
    """
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years must be between 1 and 10")

    ticker = ticker.upper()
    try:
        bars = await fetch_ohlcv(ticker, years=years)
    except TickerFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return OHLCVResponse(ticker=ticker, source="live", bar_count=len(bars), bars=bars)


@router.post("/ohlcv/universe/fetch", response_model=UniverseFetchResponse)
async def fetch_universe(years: int = 5):
    """
    Fetches all 8 candidate tickers. Sequential, not concurrent —
    yfinance/Yahoo throttles aggressive parallel requests, and this
    endpoint is a one-off backfill operation, not a hot path, so
    trading a bit of latency for reliability is the right call here.
    """
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years must be between 1 and 10")

    results: list[UniverseFetchResult] = []

    for ticker in TICKER_UNIVERSE:
        try:
            bars = await fetch_ohlcv(ticker, years=years)
            results.append(
                UniverseFetchResult(ticker=ticker, status="ok", bar_count=len(bars))
            )
        except TickerFetchError as exc:
            results.append(
                UniverseFetchResult(
                    ticker=ticker, status="failed", bar_count=0, error=str(exc)
                )
            )
        # Small pause between sequential calls to stay well under Yahoo's informal
        # rate limits — this is not the formal retry/backoff (that's the @retry
        # decorator per-call); this is spacing between different tickers.
        await asyncio.sleep(0.5)

    succeeded = sum(1 for r in results if r.status == "ok")
    failed = len(results) - succeeded
    return UniverseFetchResponse(results=results, succeeded=succeeded, failed=failed)