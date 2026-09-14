"""
Converts cached OHLCV bars into a log-return series per ticker.

Isolated from covariance.py so the "bars -> returns" transform can be
unit-tested independently of the "returns -> covariance matrix" math.
"""
import numpy as np
import pandas as pd

from modules.market_data.internal.schemas import OHLCVBar


def bars_to_price_series(bars: list[OHLCVBar]) -> pd.Series:
    """
    Adjusted close, indexed by date. Using adj_close (not close) so
    splits/dividends don't show up as fake return spikes.
    """
    if not bars:
        return pd.Series(dtype=float)

    dates = [bar.date for bar in bars]
    prices = [bar.adj_close for bar in bars]
    series = pd.Series(prices, index=pd.DatetimeIndex(dates), name="adj_close")
    return series.sort_index()


def price_series_to_log_returns(prices: pd.Series) -> pd.Series:
    """
    Log returns, not simple returns — log returns are additive across
    time and approximately normal, which is what the covariance/CVXPY
    machinery in Step 2 assumes.
    """
    if prices.empty:
        return pd.Series(dtype=float)

    log_prices = np.log(prices)
    return log_prices.diff().dropna()