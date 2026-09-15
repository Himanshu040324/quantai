"""
Orchestration layer: pulls cached OHLCV bars for the ticker universe
via market_data's public contract (never its internal/), converts
each to a log-return series, aligns them, computes the annualized
covariance matrix, and (Step 2) runs the CVXPY solver against it.

Mirrors market_data/internal/service.py's role — router.py stays a
thin HTTP layer, this is where the actual pipeline logic lives.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.market_data import TICKER_UNIVERSE, get_ohlcv_cached
from modules.optimization.internal.covariance import align_returns, compute_annualized_stats
from modules.optimization.internal.returns import bars_to_price_series, price_series_to_log_returns
from modules.optimization.internal.schemas import (
    AssetAllocation,
    CovarianceMatrixResponse,
    OptimizeResponse,
)
from modules.optimization.internal.solver import solve_markowitz

logger = logging.getLogger("quantai.optimization.service")


async def _get_aligned_stats(db: AsyncIOMotorDatabase, years: int):
    """
    Shared pipeline: fetch cached bars for the universe -> log returns
    -> align -> annualized mean/covariance. Used by both the diagnostic
    covariance endpoint and the real optimizer.
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


async def compute_covariance_matrix(
    db: AsyncIOMotorDatabase, years: int = 5
) -> CovarianceMatrixResponse:
    aligned, excluded = await _get_aligned_stats(db, years)

    if aligned.empty:
        logger.warning("No aligned return data available across universe")
        return CovarianceMatrixResponse(
            tickers=[],
            covariance=[],
            mean_returns=[],
            observation_count=0,
            excluded_tickers=excluded,
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
        # Nothing upstream should ever call this with an empty universe in
        # practice, but fail loudly rather than handing CVXPY a 0x0 problem.
        raise ValueError("No aligned return data available — cannot optimize")

    mean_returns, cov_matrix = compute_annualized_stats(aligned)
    included_tickers = list(aligned.columns)

    result = solve_markowitz(mean_returns, cov_matrix, risk_lambda)

    allocations = [
        AssetAllocation(ticker=ticker, weight=round(float(weight), 6))
        for ticker, weight in zip(included_tickers, result.weights)
    ]

    return OptimizeResponse(
        allocations=allocations,
        expected_return=result.expected_return,
        expected_variance=result.expected_variance,
        risk_lambda=risk_lambda,
        excluded_tickers=excluded,
    )