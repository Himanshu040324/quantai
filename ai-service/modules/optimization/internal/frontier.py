"""
Efficient Frontier sweep: solves solve_target_return across a range of
target returns between the min-variance and max-return portfolios.
Kept separate from solver.py (single-QP primitives) and service.py
(orchestration/I-O) so the sweep logic itself is independently testable.
"""
import logging

import numpy as np

from modules.optimization.internal.solver import (
    OptimizationError,
    SolverResult,
    solve_max_return,
    solve_min_variance,
    solve_target_return,
)

logger = logging.getLogger("quantai.optimization.frontier")


def compute_frontier(
    mean_returns: np.ndarray,
    covariance: np.ndarray,
    num_points: int = 25,
) -> list[SolverResult]:
    """
    Returns a list of SolverResult, ordered by ascending target return,
    from the min-variance portfolio to the max-return portfolio.

    Points that fail to solve (can happen right at the max-return edge
    due to solver tolerance) are skipped with a warning rather than
    aborting the whole sweep — a partial frontier is more useful than none.
    """
    min_var_result = solve_min_variance(mean_returns, covariance)
    max_return_result = solve_max_return(mean_returns, covariance)

    low = min_var_result.expected_return
    high = max_return_result.expected_return

    if high <= low:
        # Degenerate case: all assets have ~equal expected return, so the
        # frontier collapses to a single point. Return just the min-var
        # portfolio rather than dividing by a ~zero range.
        logger.warning(
            "Frontier range collapsed (low=%.6f, high=%.6f) — returning single point", low, high
        )
        return [min_var_result]

    target_returns = np.linspace(low, high, num_points)

    results = [min_var_result]
    for target in target_returns[1:-1]:
        try:
            results.append(solve_target_return(mean_returns, covariance, float(target)))
        except OptimizationError as exc:
            logger.warning("Frontier point at target_return=%.6f failed: %s", target, exc)
    results.append(max_return_result)

    return results