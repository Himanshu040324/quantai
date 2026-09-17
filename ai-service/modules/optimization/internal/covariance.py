"""
Pure linear algebra: aligned log-return series in, annualized mean
return vector + covariance matrix out (or, for CVaR, the raw scenario
matrix itself). No CVXPY, no I/O, no Mongo — solver.py/cvar_solver.py
consume this output, they don't compute it.
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


def to_scenario_matrix(aligned_returns: pd.DataFrame) -> np.ndarray:
    """
    Raw daily log returns as a T x N NumPy array (T scenarios/days, N
    assets), in the same column order as aligned_returns.columns.
    Used directly by cvar_solver.py — CVaR's LP formulation needs the
    actual scenarios, not summary statistics.

    Deliberately NOT annualized — CVaR operates on the empirical daily
    return distribution directly; annualizing would distort the tail
    shape the LP is built to capture.
    """
    return aligned_returns.to_numpy()