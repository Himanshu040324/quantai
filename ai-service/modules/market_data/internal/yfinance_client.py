"""
Thin wrapper around yfinance. This is the ONLY file in the codebase
that should import yfinance directly — router.py and everything
downstream goes through fetch_ohlcv()/fetch_fundamentals(), never
through yf.Ticker() directly. Keeps a future swap to Alpha Vantage
(the docx's named backup) to a one-file change.
"""
import logging

import pandas as pd
import yfinance as yf
from starlette.concurrency import run_in_threadpool
from tenacity import retry, stop_after_attempt, wait_exponential

from modules.market_data.internal.schemas import FundamentalsData, OHLCVBar

logger = logging.getLogger("quantai.market_data.yfinance")


class TickerFetchError(Exception):
    """Raised when yfinance returns no usable data for a ticker."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_ohlcv_sync(ticker: str, years: int) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=f"{years}y", auto_adjust=False)
    if df.empty:
        raise TickerFetchError(f"yfinance returned no data for '{ticker}'")
    return df


def _normalize_ohlcv(ticker: str, df: pd.DataFrame) -> list[OHLCVBar]:
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
    try:
        df = await run_in_threadpool(_fetch_ohlcv_sync, ticker, years)
    except TickerFetchError:
        raise
    except Exception as exc:
        logger.warning("yfinance OHLCV fetch failed for %s: %s", ticker, exc)
        raise TickerFetchError(f"Failed to fetch '{ticker}': {exc}") from exc

    return _normalize_ohlcv(ticker, df)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_fundamentals_sync(ticker: str) -> dict:
    """
    yf.Ticker(ticker).info can raise, return an empty dict, or return a
    dict missing most keys depending on the ticker/Yahoo's mood — all
    three are treated as "no usable data" and retried/raised, not
    silently passed through as a fake FundamentalsData.
    """
    info = yf.Ticker(ticker).info
    if not info or len(info) < 3:
        raise TickerFetchError(f"yfinance returned no usable info for '{ticker}'")
    return info


def _normalize_fundamentals(info: dict) -> FundamentalsData:
    """
    .get() everywhere, never info[...] — yfinance's key set genuinely
    differs by ticker type (stock vs ETF vs .NS vs US listing).
    """
    return FundamentalsData(
        pe_ratio=info.get("trailingPE"),
        forward_pe=info.get("forwardPE"),
        earnings_growth=info.get("earningsGrowth"),
        market_cap=info.get("marketCap"),
        sector=info.get("sector"),
    )


async def fetch_fundamentals(ticker: str) -> FundamentalsData:
    try:
        info = await run_in_threadpool(_fetch_fundamentals_sync, ticker)
    except TickerFetchError:
        raise
    except Exception as exc:
        logger.warning("yfinance fundamentals fetch failed for %s: %s", ticker, exc)
        raise TickerFetchError(f"Failed to fetch fundamentals for '{ticker}': {exc}") from exc

    return _normalize_fundamentals(info)