"""
Orchestration layer: pulls cached OHLCV bars for the ticker universe
via market_data's public contract (never its internal/), converts
each to a log-return series, aligns them, computes the annualized
covariance matrix, and runs the CVXPY solver / frontier sweep against it.

Mirrors market_data/internal/service.py's role — router.py stays a
thin HTTP layer, this is where the actual pipeline logic lives.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.market_data import TICKER_UNIVERSE, get_ohlcv_cached
from modules.optimization.internal.covariance import align_returns, compute_annualized_stats
from modules.optimization.internal.frontier import compute_frontier
from modules.optimization.internal.returns import bars_to_price_series, price_series_to_log_returns
from modules.optimization.internal.schemas import (
    AssetAllocation,
    CovarianceMatrixResponse,
    FrontierPoint,
    FrontierResponse,
    OptimizeResponse,
)
from modules.optimization.internal.solver import SolverResult, solve_markowitz

logger = logging.getLogger("quantai.optimization.service")


async def _get_aligned_stats(db: AsyncIOMotorDatabase, years: int):
    """
    Shared pipeline: fetch cached bars for the universe -> log returns
    -> align -> annualized mean/covariance. Used by the diagnostic
    covariance endpoint, the single-point optimizer, and the frontier sweep.
    """
    returns_by_ticker = {}

    for ticker in TICKER_UNIVERSE:
        response = await get_ohlcv_cached(db, ticker, years)
        prices = bars_to_price_series(response.bars)
        returns_by_ticker[ticker] = price_series_to_log_returns(prices)
        logger.info(
            "Fetched %d bars / %d returns for %s (source=%s)",
            response.bar_count,
            len(returns_by_ticker[ticker]),
            ticker,
            response.source,
        )

    aligned, excluded = align_returns(returns_by_ticker)
    return aligned, excluded


def _to_allocations(included_tickers: list[str], result: SolverResult) -> list[AssetAllocation]:
    return [
        AssetAllocation(ticker=ticker, weight=round(float(weight), 6))
        for ticker, weight in zip(included_tickers, result.weights)
    ]


async def compute_covariance_matrix(
    db: AsyncIOMotorDatabase, years: int = 5
) -> CovarianceMatrixResponse:
    aligned, excluded = await _get_aligned_stats(db, years)

    if aligned.empty:
        logger.warning("No aligned return data available across universe")
        return CovarianceMatrixResponse(
            tickers=[], covariance=[], mean_returns=[], observation_count=0, excluded_tickers=excluded
        )

    mean_returns, cov_matrix = compute_annualized_stats(aligned)
    included_tickers = list(aligned.columns)

    return CovarianceMatrixResponse(
        tickers=included_tickers,
        covariance=cov_matrix.tolist(),
        mean_returns=mean_returns.tolist(),
        observation_count=len(aligned),
        excluded_tickers=excluded,
    )


async def compute_optimal_allocation(
    db: AsyncIOMotorDatabase, risk_lambda: float, years: int = 5
) -> OptimizeResponse:
    aligned, excluded = await _get_aligned_stats(db, years)

    if aligned.empty:
        raise ValueError("No aligned return data available — cannot optimize")

    mean_returns, cov_matrix = compute_annualized_stats(aligned)
    included_tickers = list(aligned.columns)

    result = solve_markowitz(mean_returns, cov_matrix, risk_lambda)

    return OptimizeResponse(
        allocations=_to_allocations(included_tickers, result),
        expected_return=result.expected_return,
        expected_variance=result.expected_variance,
        risk_lambda=risk_lambda,
        excluded_tickers=excluded,
    )


async def compute_efficient_frontier(
    db: AsyncIOMotorDatabase, risk_lambda: float, years: int = 5, num_points: int = 25
) -> FrontierResponse:
    aligned, excluded = await _get_aligned_stats(db, years)

    if aligned.empty:
        raise ValueError("No aligned return data available — cannot compute frontier")

    mean_returns, cov_matrix = compute_annualized_stats(aligned)
    included_tickers = list(aligned.columns)

    frontier_results = compute_frontier(mean_returns, cov_matrix, num_points=num_points)
    frontier_points = [
        FrontierPoint(
            target_return=result.expected_return,
            expected_variance=result.expected_variance,
            allocations=_to_allocations(included_tickers, result),
        )
        for result in frontier_results
    ]

    recommended_result = solve_markowitz(mean_returns, cov_matrix, risk_lambda)
    recommended = OptimizeResponse(
        allocations=_to_allocations(included_tickers, recommended_result),
        expected_return=recommended_result.expected_return,
        expected_variance=recommended_result.expected_variance,
        risk_lambda=risk_lambda,
        excluded_tickers=excluded,
    )

    return FrontierResponse(
        tickers=included_tickers,
        frontier=frontier_points,
        recommended=recommended,
        excluded_tickers=excluded,
    )