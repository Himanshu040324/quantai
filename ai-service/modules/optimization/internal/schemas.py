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
    covariance: list[list[float]]
    mean_returns: list[float]
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


class FrontierPoint(BaseModel):
    target_return: float
    expected_variance: float
    allocations: list[AssetAllocation]


class FrontierRequest(BaseModel):
    risk_lambda: float = Field(gt=0, description="Used to compute the recommended point on the frontier")
    years: int = Field(default=5, gt=0)
    num_points: int = Field(default=25, ge=5, le=100)


class FrontierResponse(BaseModel):
    tickers: list[str]
    frontier: list[FrontierPoint]
    recommended: OptimizeResponse
    excluded_tickers: list[str]


class CvarRequest(BaseModel):
    """
    Same shape as OptimizeRequest — risk_lambda is unused by CVaR's own
    objective (CVaR has no lambda term) but is accepted for interface
    symmetry with /optimize and to select a target-return point via
    solve_cvar_target_return, keeping the two strategies comparable.
    """

    risk_lambda: float = Field(gt=0)
    years: int = Field(default=5, gt=0)


class CvarResponse(BaseModel):
    allocations: list[AssetAllocation]
    expected_return: float
    expected_variance: float
    cvar: float
    confidence_level: float
    excluded_tickers: list[str]