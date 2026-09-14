"""
Pydantic models for the optimization module.
Kept separate from router.py so schemas are reusable/importable
without pulling in FastAPI route decorators, matching market_data's pattern.
"""
from pydantic import BaseModel


class CovarianceMatrixResponse(BaseModel):
    """
    Diagnostic response for Step 1 — lets us verify the returns/covariance
    pipeline end-to-end before CVXPY (Step 2) consumes this data.
    """

    tickers: list[str]
    # annualized covariance matrix, tickers[i] x tickers[j], row-major
    covariance: list[list[float]]
    # annualized mean log return per ticker, same order as `tickers`
    mean_returns: list[float]
    # trading-day count actually used per ticker after alignment
    observation_count: int
    excluded_tickers: list[str]