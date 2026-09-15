"""
Pure CVXPY optimization logic: mean_returns + covariance + risk_lambda
in, portfolio weights out. No I/O, no Mongo, no FastAPI — testable in
isolation with known inputs/outputs, same isolation principle as
covariance.py.

Utility-form objective: maximize (expected_return - risk_lambda * variance),
i.e. classic Markowitz mean-variance utility. One solve per request;
this is distinct from Step 3's Efficient Frontier, which will sweep
target-return constraints independently of risk_lambda.
"""
import logging

import cvxpy as cp
import numpy as np

from modules.optimization.internal.constants import MAX_SINGLE_ASSET_WEIGHT

logger = logging.getLogger("quantai.optimization.solver")


class OptimizationError(Exception):
    """Raised when the QP is infeasible or the solver fails to converge."""


class SolverResult:
    def __init__(self, weights: np.ndarray, expected_return: float, expected_variance: float):
        self.weights = weights
        self.expected_return = expected_return
        self.expected_variance = expected_variance


def solve_markowitz(
    mean_returns: np.ndarray,
    covariance: np.ndarray,
    risk_lambda: float,
) -> SolverResult:
    """
    Solves: maximize (mean_returns @ w - risk_lambda * w @ covariance @ w)
    subject to: sum(w) == 1, w >= 0, w <= MAX_SINGLE_ASSET_WEIGHT

    Raises OptimizationError on infeasibility or non-optimal status —
    never silently returns a degenerate or partial solution.
    """
    n = len(mean_returns)

    if covariance.shape != (n, n):
        raise OptimizationError(
            f"Shape mismatch: mean_returns has {n} assets, covariance is {covariance.shape}"
        )

    if n * MAX_SINGLE_ASSET_WEIGHT < 1.0:
        # e.g. 3 assets at a 25% cap can never sum to 100% — infeasible by construction.
        raise OptimizationError(
            f"Infeasible constraints: {n} assets with {MAX_SINGLE_ASSET_WEIGHT:.0%} cap each "
            f"can sum to at most {n * MAX_SINGLE_ASSET_WEIGHT:.0%}, need 100%"
        )

    w = cp.Variable(n)

    portfolio_return = mean_returns @ w
    portfolio_variance = cp.quad_form(w, covariance)
    objective = cp.Maximize(portfolio_return - risk_lambda * portfolio_variance)

    constraints = [
        cp.sum(w) == 1,
        w >= 0,
        w <= MAX_SINGLE_ASSET_WEIGHT,
    ]

    problem = cp.Problem(objective, constraints)

    try:
        problem.solve()
    except cp.error.SolverError as exc:
        logger.error("CVXPY solver raised: %s", exc)
        raise OptimizationError(f"Solver failed: {exc}") from exc

    if problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        logger.error("Solver returned non-optimal status: %s", problem.status)
        raise OptimizationError(f"Optimization did not converge: status={problem.status}")

    if problem.status == cp.OPTIMAL_INACCURATE:
        logger.warning("Solver converged with OPTIMAL_INACCURATE status — result may be imprecise")

    weights = np.asarray(w.value).flatten()
    # Numerical solvers can leave tiny negative residuals (e.g. -1e-12) or
    # sums slightly off 1.0 — clip and renormalize rather than exposing
    # solver noise as a fabricated negative weight in the response.
    weights = np.clip(weights, 0, None)
    weights = weights / weights.sum()

    expected_return = float(mean_returns @ weights)
    expected_variance = float(weights @ covariance @ weights)

    return SolverResult(weights=weights, expected_return=expected_return, expected_variance=expected_variance)