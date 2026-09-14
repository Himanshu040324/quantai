"""
Orchestration layer: pulls cached OHLCV bars for the ticker universe
via market_data's public contract (never its internal/), converts
each to a log-return series, aligns them, and computes the annualized
covariance matrix.

Mirrors market_data/internal/service.py's role — router.py stays a
thin HTTP layer, this is where the actual pipeline logic lives.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.market_data import TICKER_UNIVERSE, get_ohlcv_cached
from modules.optimization.internal.covariance import align_returns, compute_annualized_stats
from modules.optimization.internal.returns import bars_to_price_series, price_series_to_log_returns
from modules.optimization.internal.schemas import CovarianceMatrixResponse

logger = logging.getLogger("quantai.optimization.service")


async def compute_covariance_matrix(
    db: AsyncIOMotorDatabase, years: int = 5
) -> CovarianceMatrixResponse:
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