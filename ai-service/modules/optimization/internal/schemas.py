"""
Pydantic models for the optimization module.
Kept separate from router.py so schemas are reusable/importable
without pulling in FastAPI route decorators, matching market_data's pattern.
"""
from pydantic import BaseModel, Field


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


class OptimizeRequest(BaseModel):
    """
    risk_lambda is the Phase 1 risk-aversion parameter (conservative 4.0
    / moderate 2.5 / aggressive 1.2), resolved and passed through by the
    Express ai-gateway from the authenticated user's stored profile.
    ai-service has no user model of its own and never looks this up —
    it only consumes the numeric value it's given.
    """

    risk_lambda: float = Field(gt=0, description="Risk-aversion coefficient, must be positive")
    years: int = Field(default=5, gt=0)


class AssetAllocation(BaseModel):
    ticker: str
    weight: float


class OptimizeResponse(BaseModel):
    allocations: list[AssetAllocation]
    expected_return: float
    expected_variance: float
    risk_lambda: float
    excluded_tickers: list[str]


class UniverseFetchResult(BaseModel):
    ticker: str
    status: str
    bar_count: int
    error: str | None = None