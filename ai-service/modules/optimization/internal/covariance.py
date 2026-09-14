"""
Pure linear algebra: aligned log-return series in, annualized mean
return vector + covariance matrix out. No CVXPY, no I/O, no Mongo —
Step 2's optimizer consumes this output, it doesn't compute it.
"""
import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def align_returns(returns_by_ticker: dict[str, pd.Series]) -> tuple[pd.DataFrame, list[str]]:
    """
    Inner-joins all tickers' return series on date so the covariance
    matrix only uses dates where every included ticker has data.

    Tickers with an empty return series (e.g. a live fetch failed and
    upstream returned no bars) are dropped rather than silently
    coercing to NaN/zero — a missing ticker must be visible, never a
    fabricated zero-variance asset.

    Returns the aligned DataFrame plus the list of tickers actually used.
    """
    valid = {ticker: series for ticker, series in returns_by_ticker.items() if not series.empty}
    excluded = [t for t in returns_by_ticker if t not in valid]

    if not valid:
        return pd.DataFrame(), []

    aligned = pd.DataFrame(valid).dropna(how="any")
    return aligned, excluded


def compute_annualized_stats(aligned_returns: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Given a DataFrame of aligned daily log returns (columns = tickers),
    returns (mean_returns, covariance_matrix), both annualized.

    Sample covariance, not shrinkage — flagged as an open decision in
    Step 1; revisit if the matrix proves ill-conditioned with only ~5yr
    of daily data across 8 tickers.
    """
    daily_mean = aligned_returns.mean().to_numpy()
    daily_cov = aligned_returns.cov().to_numpy()

    annualized_mean = daily_mean * TRADING_DAYS_PER_YEAR
    annualized_cov = daily_cov * TRADING_DAYS_PER_YEAR

    return annualized_mean, annualized_cov