"""
Thin wrapper around yfinance. This is the ONLY file in the codebase
that should import yfinance directly — router.py and everything
downstream (Phase 3's optimizer, etc.) goes through fetch_ohlcv(),
never through yf.Ticker() directly. Keeps a future swap to
Alpha Vantage (the docx's named backup) to a one-file change.
"""
import logging

import pandas as pd
import yfinance as yf
from starlette.concurrency import run_in_threadpool
from tenacity import retry, stop_after_attempt, wait_exponential

from modules.market_data.internal.schemas import OHLCVBar

logger = logging.getLogger("quantai.market_data.yfinance")


class TickerFetchError(Exception):
    """Raised when yfinance returns no usable data for a ticker."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_ohlcv_sync(ticker: str, years: int) -> pd.DataFrame:
    """
    Blocking call — yfinance has no native async API. Retries handle
    transient throttling; a real empty-data result (bad ticker) is
    not retried, it raises TickerFetchError immediately below.
    """
    df = yf.Ticker(ticker).history(period=f"{years}y", auto_adjust=False)
    if df.empty:
        raise TickerFetchError(f"yfinance returned no data for '{ticker}'")
    return df


def _normalize(ticker: str, df: pd.DataFrame) -> list[OHLCVBar]:
    """Converts yfinance's DataFrame (DateTimeIndex, capitalized columns) into our schema."""
    bars: list[OHLCVBar] = []
    for idx, row in df.iterrows():
        bars.append(
            OHLCVBar(
                date=idx.date(),
                open=round(float(row["Open"]), 4),
                high=round(float(row["High"]), 4),
                low=round(float(row["Low"]), 4),
                close=round(float(row["Close"]), 4),
                adj_close=round(float(row["Adj Close"]), 4),
                volume=int(row["Volume"]),
            )
        )
    return bars


async def fetch_ohlcv(ticker: str, years: int = 5) -> list[OHLCVBar]:
    """
    Async entry point. Runs the blocking yfinance call in a threadpool
    so it doesn't stall the event loop while other requests are in flight.
    """
    try:
        df = await run_in_threadpool(_fetch_ohlcv_sync, ticker, years)
    except TickerFetchError:
        raise
    except Exception as exc:  # yfinance can raise various network/parsing errors
        logger.warning("yfinance fetch failed for %s: %s", ticker, exc)
        raise TickerFetchError(f"Failed to fetch '{ticker}': {exc}") from exc

    return _normalize(ticker, df)